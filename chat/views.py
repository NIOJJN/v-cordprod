# chat/views.py
from django.shortcuts import render, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.paginator import Paginator
from .models import Message, DirectMessage
from servers.models import Channel
from accounts.models import User

@login_required
def direct_messages(request, user_id=None):
    friends = request.user.friends.filter(friendship_to__accepted=True)
    current_friend = None
    messages_list = []
    
    if user_id:
        current_friend = get_object_or_404(User, id=user_id)
        messages_list = DirectMessage.objects.filter(
            sender__in=[request.user, current_friend],
            recipient__in=[request.user, current_friend]
        ).order_by('timestamp')[:50]
        
        # Помечаем сообщения как прочитанные
        DirectMessage.objects.filter(
            sender=current_friend,
            recipient=request.user,
            is_read=False
        ).update(is_read=True)
    
    # Считаем непрочитанные сообщения
    unread_counts = {}
    for friend in friends:
        count = DirectMessage.objects.filter(
            sender=friend,
            recipient=request.user,
            is_read=False
        ).count()
        if count > 0:
            unread_counts[friend.id] = count
    
    context = {
        'friends': friends,
        'current_friend': current_friend,
        'messages': messages_list,
        'unread_counts': unread_counts,
    }
    return render(request, 'chat/direct_messages.html', context)

@login_required
def load_messages(request, channel_id):
    channel = get_object_or_404(Channel, id=channel_id)
    page = request.GET.get('page', 1)
    
    messages = Message.objects.filter(channel=channel).order_by('-timestamp')
    paginator = Paginator(messages, 50)
    
    try:
        messages_page = paginator.page(page)
    except:
        return JsonResponse({'error': 'Invalid page'}, status=400)
    
    messages_data = [{
        'id': msg.id,
        'content': msg.content,
        'author': msg.author.username,
        'author_id': msg.author.id,
        'avatar': msg.author.avatar.url if msg.author.avatar else None,
        'timestamp': msg.timestamp.isoformat(),
        'edited': msg.edited,
    } for msg in messages_page]
    
    return JsonResponse({
        'messages': messages_data,
        'has_next': messages_page.has_next(),
        'has_previous': messages_page.has_previous(),
    })

@login_required
def delete_message(request, message_id):
    message = get_object_or_404(Message, id=message_id)
    
    if message.author != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    message.delete()
    return JsonResponse({'success': True})

@login_required
def edit_message(request, message_id):
    if request.method != 'POST':
        return JsonResponse({'error': 'Method not allowed'}, status=405)
    
    message = get_object_or_404(Message, id=message_id)
    
    if message.author != request.user:
        return JsonResponse({'error': 'Unauthorized'}, status=403)
    
    import json
    data = json.loads(request.body)
    new_content = data.get('content')
    
    if new_content:
        message.content = new_content
        message.edited = True
        from django.utils import timezone
        message.edited_at = timezone.now()
        message.save()
        
        return JsonResponse({'success': True, 'new_content': new_content})
    
    return JsonResponse({'error': 'Content is required'}, status=400)