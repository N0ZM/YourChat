from flask import (Blueprint, render_template, redirect,
    url_for, flash, session, request, jsonify)
from sqlalchemy import and_, or_, distinct
from flask_login import current_user, login_user, logout_user, login_required
from .models import User, Message, ChatRoom, Friend, GroupMessage
from .forms import (LoginForm, MessageForm, RegisterForm,
    ChatroomForm, FriendRequestForm, UserForm, GroupMessageForm)
from app import db


bp = Blueprint('app', __name__,  url_prefix='')

@bp.route('/')
@login_required
def index():
    users = User.query.all()
    return render_template('index.html', users=users)
    
@bp.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            if user.password == form.password.data:
                login_user(user)
                return redirect(url_for('app.index'))
            else:
                flash('Invalid password.')
                return redirect(url_for('app.login'))
        else:
            flash('The email address is not registered.')
            return redirect(url_for('app.login'))
    return render_template('login.html', form=form)

@bp.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('app.login'))

@bp.route('/register', methods=['GET', 'POST'])
def register():
    form = RegisterForm()
    if form.validate_on_submit():
        user = User(
            username=form.username.data,
            email=form.email.data,
            password=form.username.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Your info is registered correctly!')
        return redirect(url_for('app.login'))
    return render_template('register.html', form=form)

@bp.route('/chat', methods=['GET', 'POST'])
@bp.route('/chat/<int:to_>', methods=['GET', 'POST'])
@login_required
def chat(to_=None):
    form = MessageForm()
    if to_:
        session['to_'] = to_
    if form.validate_on_submit():
        message = Message(
            body=form.message.data,
            from_=current_user.id,
            to_=session['to_']
            )
        db.session.add(message)
        db.session.commit()
    messages = Message.query.filter(
        or_(
            and_(
                Message.from_ == session['to_'],
                Message.to_ == current_user.id
            ),
            and_(
                Message.from_ == current_user.id,
                Message.to_ == session['to_']
            ),
        )
    )
    return render_template('chat.html', form=form, messages=messages)

@bp.route('/chatrooms', methods=['GET', 'POST'])
@login_required
def chatrooms():
    form = ChatroomForm()
    if form.validate_on_submit():
        if ChatRoom.query.filter(
                and_(
                    ChatRoom.name == form.room_name.data,
                    ChatRoom.username == current_user.username
                )
            ).first() is None:
            chatroom = ChatRoom(name=form.room_name.data, 
                username=current_user.username)
            db.session.add(chatroom)
            db.session.commit()
    room_names = db.session.query(distinct(ChatRoom.name)).all()
    users = []
    for rn in room_names:
        users.append([chat_room.username for chat_room in db.session.query(ChatRoom).filter(ChatRoom.name == rn[0]).all()])
    return render_template('chatrooms.html', form=form,
        room_names=room_names, users=users)

@bp.route('/get_friend_list', methods=['POST'])
@login_required
def get_friend_list():
    if request.method == 'POST':
        room_name = request.json.get('room_name')
        # チャットルームに登録していない友達ステータスのユーザーを検索
        chat_room = db.session.query(ChatRoom.username).filter(
            ChatRoom.name==room_name
        )
        unregister = db.session.query(User).filter(
            ~User.username.in_(chat_room)
        ).all()
        res = [ur.username for ur in unregister if Friend.is_friend(current_user, ur)]
    return jsonify(res)

@bp.route('/add_member', methods=['POST'])
@login_required
def add_member():
    if request.method == 'POST':
        room_name = request.form.get('room_name')
        members = request.form.getlist('members')
        for m in members:
            db.session.add(ChatRoom(
                name=room_name,
                username=User.query.filter_by(username=m).first().username)
            )
        db.session.commit()
    return redirect(url_for('app.chatrooms'))

@bp.route('/groupchat/<string:room_name>', methods=['GET', 'POST'])
@login_required
def groupchat(room_name):
    form = GroupMessageForm()
    if form.validate_on_submit():
        message = GroupMessage(body=form.message.data,
            username=current_user.username, chatroom=room_name)
        db.session.add(message)
        db.session.commit()
    messages = db.session.query(GroupMessage).filter(
        GroupMessage.chatroom == room_name
    )
    return render_template('groupchat.html', room_name=room_name,
        messages=messages, form=form)

@bp.route('/friends', methods=['GET', 'POST'])
@login_required
def friends():
    form = FriendRequestForm()
    # current_userが友達申請を送った相手を抽出
    send = db.session.query(Friend.receiver).filter(
        Friend.sender == current_user.id
    ).all()
    # current_userに友達申請を送った相手を抽出
    receive = db.session.query(Friend.sender).filter(
        Friend.receiver == current_user.id
    ).all()

    friends = [s[0] for s in send if s in receive]
    friends = db.session.query(User).filter(
        User.id.in_(friends)
    ).all()
    requesting = [s[0] for s in send if s not in receive]
    requesting = db.session.query(User).filter(
        User.id.in_(requesting)
    ).all()
    requested = [r[0] for r in receive if r not in send]
    requested = db.session.query(User).filter(
        User.id.in_(requested)
    ).all()
    
    if form.validate_on_submit():
        receiver = User.query.filter_by(code=form.code.data).first()
        if receiver:
            if not receiver.id == current_user.id:
                friend = Friend(
                    sender=current_user.id,
                    receiver=receiver.id
                )
                db.session.add(friend)
                db.session.commit()
            else:
                flash('You can not request yourself to be a friend!')
        else:
            flash('There is no user who has the code.')
        return redirect(url_for('app.friends'))
    return render_template('friends.html', form=form, friends=friends,
        requesting=requesting, requested=requested)

@bp.route('/delete_friend', methods=['POST'])
@login_required
def delete_friend():
    if request.method == 'POST':
        try:
            f1 = db.session.query(Friend).filter(
                Friend.sender == current_user.id,
                Friend.receiver == request.form.get('friend_id')
            ).first()
            db.session.delete(f1)
            f2 = db.session.query(Friend).filter(
                Friend.receiver == current_user.id,
                Friend.sender == request.form.get('friend_id')
            ).first()
            db.session.delete(f2)
            db.session.commit()
        except:
            db.session.rollback()
            raise
    return redirect(url_for('app.friends'))

@bp.route('/accept_user', methods=['POST'])
@login_required
def accept_user():
    if request.method == 'POST':
        friend_send = Friend(sender=current_user.id,
            receiver=request.form.get('user_id'))
        db.session.add(friend_send)
        db.session.commit()
    return redirect(url_for('app.friends'))

@bp.route('/reject_user', methods=['POST'])
@login_required
def reject_user():
    if request.method == 'POST':
        user_request = db.session.query(Friend).filter(
            Friend.sender == request.form.get('user_id'),
            Friend.receiver == current_user.id
        ).first()
        db.session.delete(user_request)
        db.session.commit()
    return redirect(url_for('app.friends'))

@bp.route('/user', methods=['GET', 'POST'])
@login_required
def user():
    form = UserForm()
    user = User.query.filter_by(id=current_user.id).first()
    if form.validate_on_submit():
        user.username = form.username.data
        user.email = form.email.data
        user.code = form.code.data
        if form.password.data:
            user.password = form.password.data
        db.session.commit()
    return render_template('user.html', form=form, user=user)

