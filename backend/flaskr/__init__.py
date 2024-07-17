import os
from flask import Flask, request, abort, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_cors import CORS
from flask_restful import Api, Resource
import random
from sqlalchemy.exc import SQLAlchemyError
from models import setup_db, Question, Category

QUESTIONS_PER_PAGE = 10

db = SQLAlchemy()

#paginate
def paginate_questions(request, query):
    page_number = request.args.get("page", 1, type=int)
    paginated_questions = query.paginate(page=page_number, per_page=QUESTIONS_PER_PAGE)
    formatted_questions = [question.format() for question in paginated_questions.items]
    return formatted_questions, paginated_questions.total

def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__)
    api = Api(app)

    if test_config is None:
        setup_db(app)
    else:
        database_path = test_config.get('SQLALCHEMY_DATABASE_URI')
        setup_db(app, database_path=database_path)

    """
    @TODO: Set up CORS. Allow '*' for origins. Delete the sample route after completing the TODOs
    """
    CORS(app, resources={'/': {'origins': '*'}})
    """
    @TODO: Use the after_request decorator to set Access-Control-Allow
    """
    @app.after_request
    def after_request(response):
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type, Authorization, true')
        response.headers.add('Access-Control-Allow-Methods', 'GET, POST, PATCH, DELETE, OPTIONS')
        return response
    """
    @TODO:
    Create an endpoint to handle GET requests
    for all available categories.
    """
    class CategoryResource(Resource):
        def get(self):
            try:
                all_categories = Category.query.order_by(Category.id).all()
                categories_dict = {category.id: category.type for category in all_categories}

                if len(categories_dict) == 0:
                    abort(404)

                return jsonify({
                    'categories': categories_dict,
                    'success': True
                })
            except SQLAlchemyError as e:
                print(e)
                abort(500)

    """
    @TODO:
    Create an endpoint to handle GET requests for questions,
    including pagination (every 10 questions).
    This endpoint should return a list of questions,
    number of total questions, current category, categories.

    TEST: At this point, when you start the application
    you should see questions and categories generated,
    ten questions per page and pagination at the bottom of the screen for three pages.
    Clicking on the page numbers should update the questions.
    """

    """
    @TODO:
    Create an endpoint to POST a new question,
    which will require the question and answer text,
    category, and difficulty score.

    TEST: When you submit a question on the "Add" tab,
    the form will clear and the question will appear at the end of the last page
    of the questions list in the "List" tab.
    """
    class QuestionListResource(Resource):
        def get(self):
            try:
                query = Question.query.order_by(Question.id)
                paginated_questions, total_questions = paginate_questions(request, query)

                if len(paginated_questions) == 0:
                    abort(404)
                
                all_categories = Category.query.all()
                categories_dict = {category.id: category.type for category in all_categories}

                return jsonify({
                    'success': True,
                    'total_questions': total_questions,
                    'categories': categories_dict,
                    'questions': paginated_questions
                })
            except SQLAlchemyError as e:
                print(e)
                abort(500)

        def post(self):
            try:
                request_body = request.get_json()
                question_text = request_body.get('question', None)
                answer_text = request_body.get('answer', None)
                difficulty_level = request_body.get('difficulty', None)
                category_id = request_body.get('category',  None)

                # check empty before insert DB
                if not question_text or not answer_text:
                    abort(400, description="The question and answer fields cannot be empty.")
                
                new_question = Question(question=question_text, answer=answer_text, difficulty=difficulty_level, category=category_id)
                new_question.insert()

                query = Question.query.order_by(Question.id)
                paginated_questions, total_questions = paginate_questions(request, query)

                return jsonify({
                    'success': True,
                    'question_created': new_question.question,
                    'created': new_question.id,
                    'questions': paginated_questions,
                    'total_questions': total_questions
                })
            except SQLAlchemyError as e:
                print(e)
                abort(422)
            except ValueError as e:
                print(e)
                abort(400, description="Invalid data provided.")
            except Exception as e:
                print(e)
                abort(500)

    """
    @TODO:
    Create an endpoint to DELETE question using a question ID.

    TEST: When you click the trash icon next to a question, the question will be removed.
    This removal will persist in the database and when you refresh the page.
    """
    class QuestionResource(Resource):
        def delete(self, question_id):
            try:
                question_to_delete = Question.query.filter_by(id=question_id).one_or_none()
                if question_to_delete is None:
                    abort(404)

                question_to_delete.delete()
                total_questions = Question.query.count()

                return jsonify({
                    'deleted': question_id,
                    'success': True,
                    'total_questions': total_questions
                })
            except SQLAlchemyError as e:
                print(e)
                abort(500)

    """
    @TODO:
    Create a POST endpoint to get questions based on a search term.
    It should return any questions for whom the search term
    is a substring of the question.

    TEST: Search by any phrase. The questions list will update to include
    only question that include that string within their question.
    Try using the word "title" to start.
    """
    class QuestionSearchResource(Resource):
        def post(self):
            try:
                request_body = request.get_json()
                search_term = request_body.get('searchTerm', None)
                
                if not search_term:
                    abort(400, description="Search term cannot be empty.")

                matched_questions = Question.query.filter(Question.question.ilike(f"%{search_term}%")).order_by(Question.id)
                paginated_questions, total_questions = paginate_questions(request, matched_questions)
                
                return jsonify({
                    'success': True,
                    'questions': paginated_questions,
                    'total_questions': total_questions
                })
            except SQLAlchemyError as e:
                print(e)
                abort(422)
            except Exception as e:
                print(e)
                abort(500)
    """
    @TODO:
    Create a GET endpoint to get questions based on category.

    TEST: In the "List" tab / main screen, clicking on one of the
    categories in the left column will cause only questions of that
    category to be shown.
    """
    class CategoryQuestionsResource(Resource):
        def get(self, category_id):
            try:
                category = Category.query.filter_by(id=category_id).one_or_none()
                if category is None:
                    abort(404)

                query = Question.query.filter_by(category=category.id).order_by(Question.id)
                paginated_questions, total_questions = paginate_questions(request, query)

                return jsonify({
                    'success': True,
                    'total_questions': total_questions,
                    'current_category': category.type,
                    'questions': paginated_questions
                })
            except SQLAlchemyError as e:
                print(e)
                abort(400)
    """
    @TODO:
    Create a POST endpoint to get questions to play the quiz.
    This endpoint should take category and previous question parameters
    and return a random questions within the given category,
    if provided, and that is not one of the previous questions.

    TEST: In the "Play" tab, after a user selects "All" or a category,
    one question at a time is displayed, the user is allowed to answer
    and shown whether they were correct or not.
    """
    class QuizResource(Resource):
        def post(self):
            try:
                request_body = request.get_json()
                previous_questions = request_body.get('previous_questions', [])
                quiz_category = request_body.get('quiz_category', None)

                next_question = get_next_question(previous_questions, quiz_category)

                return jsonify({
                    'question': next_question,
                    'success': True,
                })
            except SQLAlchemyError as e:
                print(e)
                abort(422)
            except Exception as e:
                print(e)
                abort(500)
    def get_next_question(previous_questions, quiz_category):
        """Get the next question for the quiz."""
        category_id = quiz_category['id'] if quiz_category else 0

        if category_id != 0:
            available_questions = Question.query.filter_by(category=category_id).filter(
                Question.id.notin_(previous_questions)).all()
        else:
            available_questions = Question.query.filter(
                Question.id.notin_(previous_questions)).all()

        if available_questions:
            return random.choice(available_questions).format()
        else:
            return None
    """
    @TODO:
    Create error handlers for all expected errors
    including 404 and 422.
    """
    @app.errorhandler(400)
    def bad_request_error(error):
        return jsonify({
            "success": False,
            "error": 400,
            "message": error.description if hasattr(error, 'description') else "bad request"
        }), 400

    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "success": False,
            "error": 404,
            "message": "resource not found"
        }), 404
    
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            'success': False,
            'error': 405,
            'message': 'method not allowed'
        }), 405

    @app.errorhandler(422)
    def unprocessable(error):
        return jsonify({
            "success": False,
            "error": 422,
            "message": "unprocessable"
        }), 422

    @app.errorhandler(500)
    def internal_server_error(error):
        return jsonify({
            "success": False,
            "error": 500,
            "message": "internal server error"
        }), 500

    api.add_resource(CategoryResource, '/categories')
    api.add_resource(QuestionListResource, '/questions')
    api.add_resource(QuestionSearchResource, '/questions/search')
    api.add_resource(QuestionResource, '/questions/<int:question_id>', methods=['DELETE'])
    api.add_resource(CategoryQuestionsResource, '/categories/<int:category_id>/questions')
    api.add_resource(QuizResource, '/play')
    return app

