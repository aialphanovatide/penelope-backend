"""
# Register endpoint
"""

import bcrypt
from app.utils.response_template import response_template
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from flask import Blueprint, jsonify, request
from config import Session, User
from datetime import datetime
from http import HTTPStatus

register_bp = Blueprint('register_bp', __name__)  

@register_bp.route('/register', methods=['POST'])
def register_user():
    data = request.json
    
    required_fields = ("id", "username", "email")
    missing_fields = [field for field in required_fields if field not in data]
    
    if missing_fields:
        error_message = f"Missing required fields: {', '.join(missing_fields)}"
        return response_template(
            message="Registration failed",
            error=error_message,
            status_code=HTTPStatus.BAD_REQUEST
        )
    
    with Session() as session:
        try:
            existing_user = session.query(User).filter_by(email=data["email"]).first()
            print("existing_user: ", existing_user)
            if existing_user:
                return response_template(
                    message="User already exists",
                    data=existing_user.as_dict(),
                    status_code=HTTPStatus.OK
                )
            
            hardcoded_password = "123456"
            
            # Hash the password
            hashed_password = bcrypt.hashpw(hardcoded_password.encode('utf-8'), bcrypt.gensalt())

            print("hashed_password: ", hashed_password)
            
            # Create a new user 
            new_user = User(
                id=data["id"], 
                username=data['username'],
                email=data['email'],
                picture=data.get("picture"),
                password_hash=hashed_password.decode('utf-8'),  # Store as string
            )
            
            session.add(new_user)
            session.commit()
        
            # Return the new user's information (excluding password)
            user_data = new_user.as_dict()
            user_data.pop('password_hash', None)  # Ensure password hash is not returned
            return response_template(
                message="User registered successfully",
                data=user_data,
                status_code=HTTPStatus.CREATED
            )
        
        except IntegrityError as e:
            return response_template(
                message="Integrity error",
                error=f"An unexpected error occurred: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
        
        except SQLAlchemyError as e:
            return response_template(
                message="Database error",
                error=f"An unexpected error occurred: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )
        
        except Exception as e:
            return response_template(
                message="An unexpected error occurred",
                error=f"An unexpected error occurred: {str(e)}",
                status_code=HTTPStatus.INTERNAL_SERVER_ERROR
            )