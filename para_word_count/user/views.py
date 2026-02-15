from django.shortcuts import render, redirect
from django.contrib import messages
from django.contrib.auth import authenticate, login
from django.contrib.auth.decorators import login_required
from django.contrib.auth.forms import AuthenticationForm
from .forms import UserRegisterForm
from django.core.mail import EmailMultiAlternatives
from django.template.loader import get_template
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import Paragraph, WordOccurrence
from .serializers import SearchResultSerializer
from .tasks import tokenize_paragraph
import re


def index(request):
    if request.user.is_authenticated:
        return redirect('home')
    return render(request, 'user/index.html', {'title':'index'})


def register(request):
    if request.method == 'POST':
        form = UserRegisterForm(request.POST)
        if form.is_valid():
            form.save()
            username = form.cleaned_data.get('username')
            email = form.cleaned_data.get('email')
            
            try:
                htmly = get_template('user/Email.html')
                d = { 'username': username }
                subject, from_email, to = 'welcome', 'your_email@gmail.com', email
                html_content = htmly.render(d)
                msg = EmailMultiAlternatives(subject, html_content, from_email, [to])
                msg.attach_alternative(html_content, "text/html")
                msg.send()
            except Exception as e:
                print(f"Email send failed: {str(e)}")
            
            messages.success(request, f'Your account has been created ! You are now able to log in')
            return redirect('login')
    else:
        form = UserRegisterForm()
    return render(request, 'user/register.html', {'form': form, 'title':'register here'})


def Login(request):
    if request.method == 'POST':
        username = request.POST['username']
        password = request.POST['password']
        user = authenticate(request, username = username, password = password)
        if user is not None:
            form = login(request, user)
            messages.success(request, f' welcome {username} !!')
            return redirect('home')
        else:
            messages.info(request, f'account done not exit plz sign in')
    form = AuthenticationForm()
    return render(request, 'user/login.html', {'form':form, 'title':'log in'})


def logout_user(request):
    from django.contrib.auth import logout
    logout(request)
    messages.success(request, 'You have been logged out successfully')
    return redirect('index')


@login_required(login_url='login')
def home(request):
    return render(request, 'user/home.html', {'title': 'home'})


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def save_paragraph_api(request):
    raw_text = request.data.get('raw_text', '').strip()
    
    if not raw_text:
        return Response({
            'status': 'error',
            'message': 'Please enter at least one paragraph'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    paragraphs_text = re.split(r'\n\n+', raw_text)
    paragraphs_text = [p.strip() for p in paragraphs_text if p.strip()]
    
    if not paragraphs_text:
        return Response({
            'status': 'error',
            'message': 'No valid paragraphs found'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    created_paragraphs = []
    for para_text in paragraphs_text:
        paragraph = Paragraph.objects.create(user=request.user, raw_text=para_text)
        tokenize_paragraph.delay(paragraph.id)
        created_paragraphs.append(paragraph.id)
    
    return Response({
        'status': 'success',
        'message': f'Saved and processed {len(created_paragraphs)} paragraphs successfully',
        'paragraphs_created': len(created_paragraphs),
        'paragraph_ids': created_paragraphs
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def search_word_api(request):
    word = request.query_params.get('word', '').lower().strip()
    
    if not word:
        return Response({
            'status': 'error',
            'message': 'Please provide a word parameter'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    if len(word) < 2:
        return Response({
            'status': 'error',
            'message': 'Word must be at least 2 characters'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    word_occurrences = WordOccurrence.objects.filter(
        word=word
    ).select_related('paragraph').order_by('-count')[:10]
    
    results = []
    for occurrence in word_occurrences:
        para = occurrence.paragraph
        results.append({
            'paragraph_id': para.id,
            'user_name': para.user.username,
            'raw_text': para.raw_text[:500],
            'word_count': occurrence.count,
            'created_at': para.created_at
        })
    
    return Response({
        'status': 'success',
        'word': word,
        'results_count': len(results),
        'results': results
    }, status=status.HTTP_200_OK)
