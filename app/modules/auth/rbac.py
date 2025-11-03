"""
Role-Based Access Control (RBAC)
Implements enterprise RBAC with roles and permissions
"""

from enum import Enum
from functools import wraps
from flask import session, redirect, url_for, flash, current_app
from typing import List, Set, Optional


class Role(Enum):
    """
    User roles in the system.
    
    - Admin: Full system access, user management, system settings
    - HR Manager: Employee management, trip tracking, compliance reporting
    - Employee: View own data, submit trip requests (future)
    """
    ADMIN = "admin"
    HR_MANAGER = "hr_manager"
    EMPLOYEE = "employee"


class Permission(Enum):
    """
    Granular permissions that can be assigned to roles.
    
    System Management:
    - MANAGE_USERS: Create, edit, delete users
    - MANAGE_SETTINGS: System configuration
    
    Data Management:
    - VIEW_ALL_EMPLOYEES: View all employee records
    - MANAGE_EMPLOYEES: Create, edit, delete employees
    - VIEW_ALL_TRIPS: View all trip records
    - MANAGE_TRIPS: Create, edit, delete trips
    
    Compliance:
    - VIEW_COMPLIANCE_REPORTS: Access compliance dashboards
    - EXPORT_DATA: Generate data exports
    - DELETE_DATA: Delete employee/trip data
    
    Privacy:
    - PROCESS_DSAR: Handle data subject access requests
    - ANONYMIZE_DATA: Anonymize personal data
    """
    # System
    MANAGE_USERS = "manage_users"
    MANAGE_SETTINGS = "manage_settings"
    
    # Data
    VIEW_ALL_EMPLOYEES = "view_all_employees"
    MANAGE_EMPLOYEES = "manage_employees"
    VIEW_ALL_TRIPS = "view_all_trips"
    MANAGE_TRIPS = "manage_trips"
    
    # Compliance
    VIEW_COMPLIANCE_REPORTS = "view_compliance_reports"
    EXPORT_DATA = "export_data"
    DELETE_DATA = "delete_data"
    
    # Privacy
    PROCESS_DSAR = "process_dsar"
    ANONYMIZE_DATA = "anonymize_data"


# Role-Permission Mapping
ROLE_PERMISSIONS: dict[Role, Set[Permission]] = {
    Role.ADMIN: {
        Permission.MANAGE_USERS,
        Permission.MANAGE_SETTINGS,
        Permission.VIEW_ALL_EMPLOYEES,
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_ALL_TRIPS,
        Permission.MANAGE_TRIPS,
        Permission.VIEW_COMPLIANCE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.DELETE_DATA,
        Permission.PROCESS_DSAR,
        Permission.ANONYMIZE_DATA,
    },
    Role.HR_MANAGER: {
        Permission.VIEW_ALL_EMPLOYEES,
        Permission.MANAGE_EMPLOYEES,
        Permission.VIEW_ALL_TRIPS,
        Permission.MANAGE_TRIPS,
        Permission.VIEW_COMPLIANCE_REPORTS,
        Permission.EXPORT_DATA,
        Permission.PROCESS_DSAR,
    },
    Role.EMPLOYEE: {
        # Employees can only view their own data (handled in routes)
        Permission.VIEW_COMPLIANCE_REPORTS,  # Their own compliance status
    },
}


def get_user_role(user_id: Optional[int] = None) -> Optional[Role]:
    """
    Get current user's role from session or database.
    
    Args:
        user_id: Optional user ID (defaults to session user_id)
    
    Returns:
        User's Role enum, or None if not authenticated
    """
    if user_id is None:
        user_id = session.get('user_id')
    
    if not user_id:
        return None
    
    # Check session first (performance)
    role_str = session.get('user_role')
    if role_str:
        try:
            return Role(role_str)
        except ValueError:
            pass
    
    # Fallback to database lookup
    try:
        from ..models_auth import User
        user = User.query.get(user_id)
        if user and hasattr(user, 'role'):
            role_str = user.role or Role.EMPLOYEE.value
            session['user_role'] = role_str  # Cache in session
            return Role(role_str)
    except Exception:
        pass
    
    # Default to EMPLOYEE if no role found
    return Role.EMPLOYEE


def get_user_permissions(user_id: Optional[int] = None) -> Set[Permission]:
    """
    Get all permissions for current user based on their role.
    
    Args:
        user_id: Optional user ID
    
    Returns:
        Set of Permission enums for the user
    """
    role = get_user_role(user_id)
    if not role:
        return set()
    
    return ROLE_PERMISSIONS.get(role, set())


def has_permission(permission: Permission, user_id: Optional[int] = None) -> bool:
    """
    Check if user has a specific permission.
    
    Args:
        permission: Permission to check
        user_id: Optional user ID
    
    Returns:
        True if user has permission, False otherwise
    """
    return permission in get_user_permissions(user_id)


def has_role(role: Role, user_id: Optional[int] = None) -> bool:
    """
    Check if user has a specific role.
    
    Args:
        role: Role to check
        user_id: Optional user ID
    
    Returns:
        True if user has role, False otherwise
    """
    return get_user_role(user_id) == role


def require_permission(permission: Permission):
    """
    Decorator to require a specific permission for a route.
    
    Usage:
        @require_permission(Permission.MANAGE_EMPLOYEES)
        def add_employee():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Authentication required.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not has_permission(permission):
                flash('Insufficient permissions to access this resource.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator


def require_role(role: Role):
    """
    Decorator to require a specific role for a route.
    
    Usage:
        @require_role(Role.ADMIN)
        def admin_settings():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            if not session.get('user_id'):
                flash('Authentication required.', 'warning')
                return redirect(url_for('auth.login'))
            
            if not has_role(role):
                flash('Access denied. Insufficient role.', 'danger')
                return redirect(url_for('main.dashboard'))
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

