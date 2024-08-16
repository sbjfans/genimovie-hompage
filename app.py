from flask import Flask, render_template, request, redirect, url_for, session, flash, jsonify
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from menu import menu
import json
from models import db, Influencer, Notification, CodeCategory, CodeDetail, Menu, User, Movie, MovieImage, Personnel, MoviePersonnel, Recommendation, Review, UserMovieInfo, UserPlan, Event, PointTransaction, Log
from models import db, UserMovieInfo
from models import db, Movie, MovieImage
import os
from werkzeug.utils import secure_filename
import random

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key'  # Replace with your secret key
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@10.0.66.94/moviedb'
#app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:@10.0.66.87/moviedb'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#db = SQLAlchemy(app)

db.init_app(app)  # Initialize SQLAlchemy with the app

# 파일업로드 경로 설정
UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB limit

# Ensure the upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

# 라우트 설정

# @app.route('/')
# def home():
#     return render_template('main_content.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']

        if User.query.filter_by(username=username).first() or User.query.filter_by(email=email).first():
            flash('사용자 이름 또는 이메일이 이미 존재합니다.', 'error')
            return redirect(url_for('register'))

        hashed_password = generate_password_hash(password, method='pbkdf2:sha256')
        new_user = User(username=username, email=email, password_hash=hashed_password)

        db.session.add(new_user)
        db.session.commit()

        log_action(new_user.user_id, '회원가입 성공')

        flash('회원가입 성공! 로그인 해주세요.', 'success')
        return redirect(url_for('login'))

    return render_template('register.html')

# 로그 기록 함수
def log_action(user_id, action):
    log_entry = Log(user_id=user_id, action=action)
    db.session.add(log_entry)
    db.session.commit()

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()

        if user and check_password_hash(user.password_hash, password):
            session['user_id'] = user.user_id
            log_action(user.user_id, '로그인 성공')
            flash('로그인 성공!', 'success')
            return redirect(url_for('index'))
        else:
            flash('사용자 이름이나 비밀번호가 잘못되었습니다.', 'danger')

    return render_template('login.html')

@app.route('/logout')
def logout():
    user_id = session.pop('user_id', None)
    if user_id:
        log_action(user_id, '로그아웃')
    flash('로그아웃 되었습니다.', 'info')
    return redirect(url_for('login'))

@app.route('/logs')
def logs():
    log_entries = Log.query.order_by(Log.timestamp.desc()).all()
    return render_template('logs.html', logs=log_entries)


@app.route('/create_code_categories', methods=['GET', 'POST'])
def create_code_categories():
    if request.method == 'POST':

        print('분류코드 저장::')

        category_name = request.form['category_name']
        description = request.form['description']
        is_active = request.form['is_active']

        if is_active=='on':
            is_active=1
        else :
            is_active=0    

        print('category_name::'+category_name)
        print('description::'+description)
        print('is_active::'+str(is_active))
        
        new_category = CodeCategory(category_name=category_name, description=description, is_active=is_active)
        db.session.add(new_category)
        db.session.commit()
        
        return redirect(url_for('search_code_categories'))

    categories = CodeCategory.query.all()
    return render_template('code_categories_list.html', categories=categories)

@app.route('/search_code_categories', methods=['GET', 'POST'])
def search_code_categories():

    print('코드분류 조회::')

    category_id = ''
    category_name = ''
    description = ''
    is_active = ''

    if request.method == 'POST':
        category_id = request.form.get('search_category_id', '')
        category_name = request.form.get('search_category_name', '')
        description = request.form.get('search_description', '')
        is_active = request.form.get('is_active', '')

        print('category_id::'+category_id)
        print('category_name::'+category_name)
        print('description::'+description)
        print('is_active::'+str(is_active))

    query = CodeCategory.query

    if category_id:
        query = query.filter(CodeCategory.category_id.ilike(f'%{category_id}%'))
    if category_name:
        query = query.filter(CodeCategory.category_name.ilike(f'%{category_name}%'))
    if description:
        query = query.filter(CodeCategory.description.ilike(f'%{description}%'))
    if is_active != '':
        query = query.filter(CodeCategory.is_active == is_active)

    categories = query.all()

    print('query='+str(query))   
    '''
    query=SELECT tb_code_categories.category_id AS tb_code_categories_category_id, tb_code_categories.category_name AS tb_code_categories_category_name, tb_code_categories.description AS tb_code_categories_description, tb_code_categories.is_active AS tb_code_categories_is_active
    FROM tb_code_categories
    '''

    return render_template('code_categories_list.html', 
                           categories=categories, 
                           search_category_id=category_id, 
                           search_category_name=category_name, 
                           search_description=description, 
                           search_is_active=is_active)


@app.route('/select_category_list', methods=['GET'])
def select_categories_list():
    print('코드분류목록조회::')

    # Query all categories
    categories = CodeCategory.query.all()

    # Convert the query result to a list of dictionaries
    category_list = [
        {
            'category_id': category.category_id,
            'category_name': category.category_name
        }
        for category in categories
    ]

    # Print the query for debugging
    print('categories=' + str(category_list))

    # Return the list of categories as JSON
    return jsonify({'categories': category_list})


# 인플루언서
@app.route('/create_influencer', methods=['POST'])
def create_influencer():
    if request.method == 'POST':
        name = request.form['name']
        bio = request.form['bio']
        img_path=''
        
        # Handle the file upload
        if 'photo' not in request.files:
            return "No file part"
        file = request.files['photo']
        if file.filename == '':
            return "No selected file"
        if file:
            filename = secure_filename(file.filename)
            file.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
            img_path = '/'+UPLOAD_FOLDER
            # Save to database
            new_influencer = Influencer(name=name, bio=bio, img_path=img_path, img_nm=filename)
            db.session.add(new_influencer)
            db.session.commit()
            
            return redirect(url_for('search_influencers'))
    
    return render_template('influencers_list.html')

@app.route('/search_influencers', methods=['GET', 'POST'])
def search_influencers():

    print('인플루언서 조회::')
    
    name = ''

    if request.method == 'POST':
        
        name = request.form.get('search_name', '')
        
        print('name::'+name)
       
    query = Influencer.query

    if name:
        query = query.filter(Influencer.name.ilike(f'%{name}%'))
    

    influencers = query.all()

    print('query='+str(query))   
   
    return render_template('influencers_list.html',     
                           influencers=influencers,                        
                           search_name=name 
                          )





# 영화 조회
@app.route('/search_movies', methods=['GET', 'POST'])
def search_movies():
    print('영화 조회::')

    movie_id = ''
    title = ''
    director_name = ''

    if request.method == 'POST':
        movie_id = request.form.get('search_movie_id', '')
        title = request.form.get('search_title', '')
        director_name = request.form.get('search_director_name', '')

        print('movie_id::' + movie_id)
        print('title::' + title)
        print('director_name::' + director_name)

    query = db.session.query(
        Movie.movie_id,
        Movie.title,
        Movie.genre,
        Movie.release_date,
        db.func.coalesce(db.func.round(db.func.avg(Review.rating) * 2) / 2, 0).label('average_rating'),
        Personnel.name.label('director_name'),
        MovieImage.image_url  # 이미지 URL 추가
    ).outerjoin(Review, Movie.movie_id == Review.movie_id)\
     .outerjoin(MoviePersonnel, Movie.movie_id == MoviePersonnel.movie_id)\
     .outerjoin(Personnel, db.and_(MoviePersonnel.personnel_id == Personnel.personnel_id, Personnel.role_code == 'director'))\
     .outerjoin(MovieImage, Movie.movie_id == MovieImage.movie_id).group_by(Movie.movie_id, Personnel.name, MovieImage.image_url)  

    if movie_id:
        query = query.filter(Movie.movie_id.ilike(f'%{movie_id}%'))
    if title:
        query = query.filter(Movie.title.ilike(f'%{title}%'))
    if director_name:
        query = query.filter(Personnel.name.ilike(f'%{director_name}%'))

    movies = query.all()

    print('query=' + str(query))

    return render_template('movies_list.html',
                           movies=movies,
                           search_movie_id=movie_id,
                           search_title=title,
                           search_director_name=director_name)


# 가상 데이터 _user_reviews
# 임의의 데이터 
users_reviews = [
    {'user_id': 1, 'username': 'Alice'},
    {'user_id': 2, 'username': 'Bob'},
    {'user_id': 3, 'username': 'Charlie'}
]

movies_reviews = [
    {'movie_id': 1, 'title': 'Inception'},
    {'movie_id': 2, 'title': 'Titanic'},
    {'movie_id': 3, 'title': 'Avengers: Endgame'},
    {'movie_id': 4, 'title': 'Parasite'},
    {'movie_id': 5, 'title': 'Joker'}
]

reviews_reviews = [
    {'review_id': 1, 'user_id': 1, 'movie_id': 1, 'username': 'Alice', 'movie_title': 'Inception', 'review_text': 'Great movie!', 'rating': 9.0},
    {'review_id': 2, 'user_id': 2, 'movie_id': 2, 'username': 'Bob', 'movie_title': 'Titanic', 'review_text': 'Very emotional.', 'rating': 8.5}
]


@app.route('/user_reviews')
def user_reviews():
    return render_template('user_reviews.html', users=users_reviews, movies=movies_reviews, reviews=reviews_reviews)

@app.route('/submit_review', methods=['POST'])
def submit_review():
    author_name = request.form['author_name']
    movie_title = request.form['movie_title']
    review_text = request.form['review_text']
    rating = request.form['rating']

    # 리뷰 추가 (실제 데이터베이스 연동 필요)
    new_review = {
        'review_id': len(reviews_reviews) + 1,
        'user_id': next(user['user_id'] for user in users_reviews if user['username'] == author_name),
        'movie_id': next(movie['movie_id'] for movie in movies_reviews if movie['title'] == movie_title),
        'username': author_name,
        'movie_title': movie_title,
        'review_text': review_text,
        'rating': float(rating)
    }
    reviews_reviews.append(new_review)

    return redirect(url_for('user_reviews'))

@app.route('/update_user_review', methods=['POST'])
def update_user_review():
    review_id = int(request.form['review_id'])
    review_text = request.form['review_text']
    rating = request.form['rating']

    for review in reviews_reviews:
        if review['review_id'] == review_id:
            review['review_text'] = review_text
            review['rating'] = float(rating)
            break

    return redirect(url_for('user_reviews'))

@app.route('/delete_user_review', methods=['POST'])
def delete_user_review():
    review_id = int(request.form['review_id'])
    global reviews_reviews
    reviews_reviews = [review for review in reviews_reviews if review['review_id'] != review_id]

    return redirect(url_for('user_reviews'))

# @app.route('/')
# def index():
#     return render_template('main.html')

# 유저 리뷰 조회
@app.route('/reviews', methods=['GET', 'POST'])
def reviews():
    if request.method == 'POST':
        # 폼에서 검색 조건 가져오기
        search_user_name = request.form.get('search_user_name', '').strip()
        search_movie_name = request.form.get('search_movie_name', '').strip()

def render_template_for_menu(template_name, **kwargs):
    """템플릿 렌더링을 위한 공통 함수. 동적 컨텍스트를 처리."""
    return render_template(template_name, **kwargs)

@app.route('/')
def home():
    view = request.args.get('view', 'main')  # 'view' 쿼리 파라미터로 어떤 페이지를 렌더링할지 결정

    # 각 뷰 이름에 대한 템플릿 파일 매핑
    view_templates = {
        'code_categories_list': 'code_categories_list.html',
        'code_details_list': 'code_details_list.html',
        'menus_list': 'menus_list.html',
        'users_list': 'users_list.html',
        'social_network_list': 'social_network_list.html',
        'login_log_list': 'login_log_list.html',
        'movies_list': 'movies_list.html',
        'movies_list_pop': 'movies_list_pop.html',
        'movie_review_list': 'movie_review_list.html',
        'movie_recommendations_list': 'movie_recommendations_list.html',
        'user_movie_info_list': 'user_movie_info_list.html',
        'movie_person_list': 'movie_person_list.html',
        'event_list': 'event_list.html',
        'influencers_list': 'influencers_list.html',
        'login': 'login.html',
        'user_reviews': 'user_reviews.html',
        'social_links': 'social_links.html',
        'custom_recommendations': 'custom_recommendations.html',
        'points_management': 'points_management.html',
        'notifications': 'notification_list.html',
        'other': 'other_content.html'  # 기본 템플릿
    }

    # 현재 뷰에 맞는 템플릿 파일 찾기
    template_file = view_templates.get(view, 'main.html')

    if view == 'main':
        json_path = os.path.join(app.static_folder, 'json', 'moviedb.json')  # JSON 파일 경로

        if not os.path.exists(json_path):
            return f"JSON file not found at {json_path}", 404

        try:
            with open(json_path, 'r', encoding='utf-8') as file:
                data = json.load(file)
        except json.JSONDecodeError:
            return "Error decoding JSON file.", 500

        # 영화 제목을 랜덤하게 선택
        movie_data = [movie for movie in data if 'title' in movie]
        selected_movies = random.sample(movie_data, min(47, len(movie_data)))  # 총 47개의 영화 데이터 선택

        # 랜덤 이미지 경로 생성 함수
        def get_random_images(count=5):
            base_path = 'images/random'
            return [f"{base_path}{i+1}.jpg" for i in range(count)]

        # 랜덤 퍼센트 계산
        comp_percentage_1 = random.randint(40, 60)
        comp_percentage_2 = 100 - comp_percentage_1

        # 영화 제목을 rank_movie_1 ~ 20으로 전달
        context = {
            'movies': [
                {
                    'movie_id': movie['movie_id'],
                    'title': movie['title'],
                    'recommendations': random.randint(500, 990)
                } for movie in selected_movies[:5]
            ],
            'rank_movies': [
                {
                    'movie_id': movie['movie_id'],
                    'title': movie['title'],
                    'images': get_random_images()
                } for movie in selected_movies[5:45]
            ],
            'comp_movie_title_1': selected_movies[5],
            'comp_movie_title_2': selected_movies[6],
            'comp_percentage_1': comp_percentage_1,
            'comp_percentage_2': comp_percentage_2,
        }

        return render_template_for_menu('main_content.html', **context)
    else:
        return render_template_for_menu(template_file)


def create_app():
    app.register_blueprint(menu, url_prefix='/menu')  # 블루프린트 등록
    return app

if __name__ == '__main__':
    logging.basicConfig(level=logging.DEBUG)
    app = create_app()
    
    app.run(debug=True)


