# accounts/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import User, Friendship, FriendRequest
from .forms import UserRegistrationForm, UserProfileForm

def register(request):
    if request.method == 'POST':
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешна!')
            return redirect('home')
    else:
        form = UserRegistrationForm()
    return render(request, 'accounts/register.html', {'form': form})

@login_required
def profile(request, user_id):
    user = get_object_or_404(User, id=user_id)
    is_friend = Friendship.objects.filter(
        from_user=request.user, 
        to_user=user, 
        accepted=True
    ).exists()
    
    sent_request = FriendRequest.objects.filter(
        from_user=request.user,
        to_user=user,
        accepted=False,
        declined=False
    ).exists()
    
    context = {
        'profile_user': user,
        'is_friend': is_friend,
        'sent_request': sent_request,
    }
    return render(request, 'accounts/profile.html', context)

@login_required
def edit_profile(request):
    if request.method == 'POST':
        form = UserProfileForm(request.POST, request.FILES, instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request, 'Профиль обновлен!')
            return redirect('profile', user_id=request.user.id)
    else:
        form = UserProfileForm(instance=request.user)
    return render(request, 'accounts/edit_profile.html', {'form': form})

@login_required
def send_friend_request(request, user_id):
    if request.method == 'POST':
        to_user = get_object_or_404(User, id=user_id)
        
        # Проверяем, не отправили ли уже запрос
        if FriendRequest.objects.filter(from_user=request.user, to_user=to_user).exists():
            return JsonResponse({'success': False, 'error': 'Запрос уже отправлен'})
        
        # Проверяем, не друзья ли уже
        if Friendship.objects.filter(from_user=request.user, to_user=to_user, accepted=True).exists():
            return JsonResponse({'success': False, 'error': 'Вы уже друзья'})
        
        FriendRequest.objects.create(from_user=request.user, to_user=to_user)
        return JsonResponse({'success': True})
    
    return JsonResponse({'success': False})

@login_required
def accept_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    
    friend_request.accepted = True
    friend_request.save()
    
    # Создаем дружбу в обе стороны
    Friendship.objects.get_or_create(
        from_user=friend_request.from_user,
        to_user=friend_request.to_user,
        defaults={'accepted': True}
    )
    Friendship.objects.get_or_create(
        from_user=friend_request.to_user,
        to_user=friend_request.from_user,
        defaults={'accepted': True}
    )
    
    return JsonResponse({'success': True})

@login_required
def decline_friend_request(request, request_id):
    friend_request = get_object_or_404(FriendRequest, id=request_id, to_user=request.user)
    friend_request.declined = True
    friend_request.save()
    return JsonResponse({'success': True})

@login_required
def search_users(request):
    query = request.GET.get('q', '')
    users = []
    
    if query:
        users = User.objects.filter(username__icontains=query).exclude(id=request.user.id)[:20]
    
    context = {
        'users': users,
        'query': query,
    }
    return render(request, 'accounts/search.html', context)