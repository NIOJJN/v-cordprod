from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from .models import Server, Channel, Category, ServerMember
from accounts.models import User


@login_required
def home(request):
    servers = request.user.servers.all()
    friends = request.user.friends.filter(friendship_to__accepted=True)
    friend_requests = request.user.received_requests.filter(accepted=False, declined=False)
    
    context = {
        'servers': servers,
        'friends': friends,
        'friend_requests': friend_requests,
    }
    return render(request, 'servers/home.html', context)


@login_required
def server_view(request, server_id, channel_id=None):
    server = get_object_or_404(Server, id=server_id)
    
    # Проверяем, является ли пользователь участником
    if not ServerMember.objects.filter(server=server, user=request.user).exists():
        messages.error(request, 'Вы не участник этого сервера')
        return redirect('home')
    
    categories = server.categories.all()
    channels = server.channels.all()
    
    if channel_id:
        current_channel = get_object_or_404(Channel, id=channel_id, server=server)
    else:
        current_channel = channels.filter(channel_type='text').first()
    
    messages_list = []
    if current_channel:
        from chat.models import Message
        messages_list = Message.objects.filter(channel=current_channel).order_by('timestamp')[:50]
    
    members = ServerMember.objects.filter(server=server).select_related('user')
    is_owner = server.owner == request.user
    
    context = {
        'server': server,
        'categories': categories,
        'channels': channels,
        'current_channel': current_channel,
        'messages': messages_list,
        'members': members,
        'is_owner': is_owner,
    }
    return render(request, 'servers/server.html', context)


@login_required
def create_server(request):
    if request.method == 'POST':
        name = request.POST.get('name')
        description = request.POST.get('description', '')
        
        if name:
            # Создаём сервер
            server = Server.objects.create(
                name=name,
                owner=request.user,
                description=description
            )
            
            # Добавляем владельца как участника
            ServerMember.objects.create(
                user=request.user,
                server=server,
                role='owner'
            )
            
            # Создаём категорию по умолчанию
            category = Category.objects.create(
                server=server,
                name='Основные',
                position=0
            )
            
            # Создаём текстовый канал
            Channel.objects.create(
                server=server,
                category=category,
                name='общий',
                channel_type='text',
                position=0
            )
            
            # Создаём голосовой канал
            Channel.objects.create(
                server=server,
                category=category,
                name='Голосовой',
                channel_type='voice',
                position=1
            )
            
            messages.success(request, f'Сервер "{name}" создан!')
            return redirect('server_view', server_id=server.id)
    
    return redirect('home')


@login_required
def create_channel(request, server_id):
    server = get_object_or_404(Server, id=server_id)
    
    # Проверяем права
    if not ServerMember.objects.filter(server=server, user=request.user).exists():
        return JsonResponse({'success': False, 'error': 'Нет доступа'})
    
    if request.method == 'POST':
        name = request.POST.get('name')
        channel_type = request.POST.get('channel_type', 'text')
        category_id = request.POST.get('category')
        
        if name:
            category = None
            if category_id:
                category = get_object_or_404(Category, id=category_id, server=server)
            
            channel = Channel.objects.create(
                server=server,
                name=name,
                channel_type=channel_type,
                category=category
            )
            
            return JsonResponse({
                'success': True,
                'channel_id': channel.id,
                'channel_name': channel.name
            })
    
    return JsonResponse({'success': False, 'error': 'Нет названия'})


@login_required
def join_server(request, invite_code):
    """Присоединение к серверу по коду приглашения"""
    try:
        server = Server.objects.get(invite_code=invite_code)
        
        # Проверяем, не участник ли уже
        if ServerMember.objects.filter(server=server, user=request.user).exists():
            messages.info(request, f'Вы уже участник сервера "{server.name}"')
        else:
            # Добавляем как участника
            ServerMember.objects.create(
                user=request.user,
                server=server,
                role='member'
            )
            messages.success(request, f'Вы присоединились к серверу "{server.name}"!')
        
        return redirect('server_view', server_id=server.id)
        
    except Server.DoesNotExist:
        messages.error(request, 'Сервер с таким кодом не найден')
        return redirect('home')


@login_required
def join_server_by_code(request):
    """Присоединение к серверу через POST запрос"""
    if request.method == 'POST':
        code = request.POST.get('code', '').strip()
        if code:
            return join_server(request, code)
    
    return redirect('home')