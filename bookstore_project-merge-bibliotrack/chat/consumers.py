import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from .models import Message, BookClub, Comment, Like, Reply, Notification
from django.contrib.auth.models import User
from django.utils import timezone

class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.book_id = self.scope['url_route']['kwargs']['book_id']
        self.room_group_name = f'chat_{self.book_id}'

        # Join room group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        # Leave room group
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive message from WebSocket
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        message = text_data_json['message']
        user = self.scope['user']

        # Save message to database
        await self.save_message(message, user)

        # Send message to room group
        await self.channel_layer.group_send(
            self.room_group_name,
            {
                'type': 'chat_message',
                'message': message,
                'user': user.username
            }
        )

    # Receive message from room group
    async def chat_message(self, event):
        message = event['message']
        user = event['user']

        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'message': message,
            'user': user
        }))

    @database_sync_to_async
    def save_message(self, message, user):
        book_club = BookClub.objects.get(book_id=self.book_id)
        Message.objects.create(
            book_club=book_club,
            user=user,
            content=message
        )

class NotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        if self.user.is_authenticated:
            self.room_group_name = f'notifications_{self.user.id}'

            # Join user's notification group
            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.accept()

    async def disconnect(self, close_code):
        if hasattr(self, 'room_group_name'):
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    # Send notification to user
    async def send_notification(self, event):
        notification = event['notification']

        # Send notification to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'notification',
            'notification': notification
        }))

class CommentConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.book_id = self.scope['url_route']['kwargs']['book_id']
        self.room_group_name = f'comments_{self.book_id}'

        # Join book comments group
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )

        await self.accept()

    async def disconnect(self, close_code):
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    # Receive comment/like/reply actions
    async def receive(self, text_data):
        text_data_json = json.loads(text_data)
        action = text_data_json['action']
        user = self.scope['user']

        if action == 'new_comment':
            comment_data = await self.save_comment(text_data_json, user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_update',
                    'action': 'new_comment',
                    'comment': comment_data
                }
            )
        elif action == 'like_comment':
            like_data = await self.toggle_like(text_data_json, user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_update',
                    'action': 'like_update',
                    'like_data': like_data
                }
            )
        elif action == 'new_reply':
            reply_data = await self.save_reply(text_data_json, user)
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'comment_update',
                    'action': 'new_reply',
                    'reply': reply_data
                }
            )

    # Handle comment updates
    async def comment_update(self, event):
        # Send update to WebSocket
        await self.send(text_data=json.dumps(event))

    @database_sync_to_async
    def save_comment(self, data, user):
        from books.models import Book
        book = Book.objects.get(id=self.book_id)
        content = data['content']

        comment = Comment.objects.create(
            book=book,
            user=user,
            content=content
        )

        # Create notifications for other commenters
        other_commenters = Comment.objects.filter(book=book)\
            .exclude(user=user)\
            .values_list('user', flat=True)\
            .distinct()

        for commenter_id in other_commenters:
            Notification.objects.create(
                user_id=commenter_id,
                notification_type='comment',
                title='New Comment',
                message=f'{user.username} commented on "{book.title}"',
                related_object_id=comment.id,
                related_object_type='comment'
            )

        return {
            'id': comment.id,
            'user': comment.user.username,
            'content': comment.content,
            'created_at': comment.created_at.isoformat(),
            'likes_count': 0,
            'replies_count': 0
        }

    @database_sync_to_async
    def toggle_like(self, data, user):
        comment_id = data['comment_id']
        comment = Comment.objects.get(id=comment_id)
        like, created = Like.objects.get_or_create(
            comment=comment,
            user=user
        )

        if not created:
            like.delete()
            comment.likes_count = max(0, comment.likes_count - 1)
            liked = False
        else:
            comment.likes_count += 1
            liked = True

            # Create notification if liking someone else's comment
            if comment.user != user:
                Notification.objects.create(
                    user=comment.user,
                    notification_type='like',
                    title='Comment Liked',
                    message=f'{user.username} liked your comment on "{comment.book.title}"',
                    related_object_id=comment.id,
                    related_object_type='comment'
                )

        comment.save()

        return {
            'comment_id': comment_id,
            'liked': liked,
            'likes_count': comment.likes_count
        }

    @database_sync_to_async
    def save_reply(self, data, user):
        comment_id = data['comment_id']
        content = data['content']
        comment = Comment.objects.get(id=comment_id)

        reply = Reply.objects.create(
            comment=comment,
            user=user,
            content=content
        )

        comment.replies_count += 1
        comment.save()

        # Create notification for comment author
        if comment.user != user:
            Notification.objects.create(
                user=comment.user,
                notification_type='reply',
                title='New Reply',
                message=f'{user.username} replied to your comment on "{comment.book.title}"',
                related_object_id=reply.id,
                related_object_type='reply'
            )

        return {
            'id': reply.id,
            'comment_id': comment_id,
            'user': reply.user.username,
            'content': reply.content,
            'created_at': reply.created_at.isoformat()
        }
