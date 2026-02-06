from authlib.integrations.starlette_client import OAuth
from starlette.config import Config
from starlette.requests import Request
from starlette.responses import RedirectResponse
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from src.config import settings
from src.database import get_db
from src.models import User, RoleEnum

router = APIRouter()

# Authlib Configuration
# Note: In production, use environment variables.
config_data = {
    'MS_CLIENT_ID': settings.MS_CLIENT_ID,
    'MS_CLIENT_SECRET': settings.MS_CLIENT_SECRET,
    'MS_TENANT_ID': settings.MS_TENANT_ID
}
starlette_config = Config(environ=config_data)
oauth = OAuth(starlette_config)

oauth.register(
    name='microsoft',
    client_id=settings.MS_CLIENT_ID,
    client_secret=settings.MS_CLIENT_SECRET,
    server_metadata_url=f'https://login.microsoftonline.com/{settings.MS_TENANT_ID}/v2.0/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile User.Read'}
)

@router.get("/dev_login")
async def dev_login(request: Request, db: Session = Depends(get_db)):
    """Bypass login for development."""
    # Find or Create Admin
    email = "admin@calasanz.edu.co"
    user = db.query(User).filter(User.email == email).first()
    
    if not user:
        # Create if not exists (should exist from dummy_data)
        user = User(
            email=email,
            full_name="Admin Global (Dev)",
            role=RoleEnum.ADMIN_GLOBAL
        )
        db.add(user)
        db.commit()
        db.refresh(user)
    
    # Set Session
    request.session['user'] = {
        "id": user.id,
        "email": user.email,
        "name": user.full_name,
        "role": user.role.value
    }
    
    return RedirectResponse(url='/dashboard')

@router.get("/login")
async def login(request: Request):
    redirect_uri = request.url_for('auth_callback')
    return await oauth.microsoft.authorize_redirect(request, redirect_uri)

@router.get("/callback")
async def auth_callback(request: Request, db: Session = Depends(get_db)):
    try:
        token = await oauth.microsoft.authorize_access_token(request)
        user_info = token.get('userinfo')
        if not user_info:
            # Fallback if userinfo not in token (depends on scope/claim)
            # You might need to call graph api here if profile is missing
            user_info = parse_id_token(token) 
        
        # Check if user exists, else create/update
        user = db.query(User).filter(User.email == user_info['email']).first()
        if not user:
            # Auto-provision logic (or error if strict)
            # For now, auto-provision as Docente
            user = User(
                email=user_info['email'],
                full_name=user_info.get('name', 'Unknown'),
                oid_sub=user_info.get('sub'),
                role=RoleEnum.DOCENTE
            )
            db.add(user)
            db.commit()
            db.refresh(user)
        
        # Store user in session
        request.session['user'] = {
            "id": user.id,
            "email": user.email,
            "name": user.full_name,
            "role": user.role.value
        }
        
        return RedirectResponse(url='/dashboard')
    except Exception as e:
        print(f"Auth Error: {e}")
        return RedirectResponse(url='/?error=auth_failed')

@router.get("/logout")
async def logout(request: Request):
    request.session.pop('user', None)
    return RedirectResponse(url='/')

def get_current_user(request: Request):
    user = request.session.get('user')
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Not authenticated")
    return user

def parse_id_token(token):
    # Depending on authlib version, userinfo might be inside 'id_token' claims
    return token.get('userinfo') or {}
