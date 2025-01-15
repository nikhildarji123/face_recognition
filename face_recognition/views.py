from django.shortcuts import render
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.core.files.base import ContentFile
from django.core.exceptions import ObjectDoesNotExist
import os
import cv2
import tempfile
from .models import User, UserImages
import face_recognition
import base64

@csrf_exempt  # Bypass CSRF protection for this endpoint
def register(request):
    if request.method == 'POST':
        # Safely retrieve form data
        username = request.POST.get('username')
        face_image_data = request.POST.get('face_image')


        # Validate input
        if not username or not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Username or face image is missing'
            }, status=400)

        try:
            # Decode base64 image
            face_image_data = face_image_data.split(",")[1]  # Extract only the base64-encoded part
            face_image = ContentFile(base64.b64decode(face_image_data), name=f'{username}.jpg')
        except (IndexError, ValueError) as e:
            return JsonResponse({
                'status': 'error',
                'message': 'Invalid face image data'
            }, status=400)

        try:
            # Check if the username already exists
            user, created = User.objects.get_or_create(username=username)
            if not created:
                return JsonResponse({
                    'status': 'error',
                    'message': 'Username is already taken'
                }, status=400)

            # Check if the user already has an associated image
            if UserImages.objects.filter(user=user).exists():
                return JsonResponse({
                    'status': 'error',
                    'message': 'User already has an image registered'
                }, status=400)

            # Save the face image and associate it with the user
            UserImages.objects.create(user=user, face_image=face_image)
            return JsonResponse({
                'status': 'success',
                'message': 'User registered successfully'
            }, status=201)

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error during registration: {str(e)}'
            }, status=500)

    # Render the registration page if the request is GET
    return render(request, 'register.html')

@csrf_exempt
def login(request):
    if request.method == 'POST':
        face_image_data = request.POST.get('face_image')

        if not face_image_data:
            return JsonResponse({
                'status': 'error',
                'message': 'Face image is missing.'
            })

        try:
            face_image_data = face_image_data.split(",")[1]  # Extract base64 data
            face_image = base64.b64decode(face_image_data)

            # Save the uploaded face temporarily for recognition in a predefined directory
            user_faces_dir = 'C:\\Users\\Nikhil Darji\\Documents\\Nikhil Darji\\flogin\\user_faces\\'
            if not os.path.exists(user_faces_dir):
                os.makedirs(user_faces_dir)

            # Generate a unique filename for the uploaded face image
            user_face_path = os.path.join(user_faces_dir, 'temp_user_face.jpg')

            # Save the image temporarily
            with open(user_face_path, 'wb') as user_face_file:
                user_face_file.write(face_image)

            print(f"Temporary image path: {user_face_path}")

            # Ensure that the file exists and points to a valid path
            if not os.path.exists(user_face_path):
                return JsonResponse({
                    'status': 'error',
                    'message': 'Temporary file could not be created.'
                })

            # Load the captured face for encoding
            captured_face = face_recognition.load_image_file(user_face_path)
            captured_encoding = face_recognition.face_encodings(captured_face)

            # Delete the temporary file after encoding
            os.remove(user_face_path)

            if len(captured_encoding) == 0:
                return JsonResponse({
                    'status': 'error',
                    'message': 'No face detected in the image.'
                })

            captured_encoding = captured_encoding[0]

            # Compare with stored user images
            users = UserImages.objects.all()
            for user in users:
                stored_face_path = user.face_image.path
                if not os.path.exists(stored_face_path):
                    continue  # Skip invalid paths or missing files

                stored_face = face_recognition.load_image_file(stored_face_path)
                stored_encoding = face_recognition.face_encodings(stored_face)

                if len(stored_encoding) == 0:
                    continue

                stored_encoding = stored_encoding[0]
                results = face_recognition.compare_faces([stored_encoding], captured_encoding)
                if results[0]:  # If a match is found
                    return JsonResponse({
                        'status': 'success',
                        'message': f'Welcome back, {user.user.username}!'
                    })

            return JsonResponse({
                'status': 'error',
                'message': 'No matching face found. Please register first.'
            })

        except Exception as e:
            return JsonResponse({
                'status': 'error',
                'message': f'Error during login: {str(e)}'
            })

    return render(request, 'login.html')
