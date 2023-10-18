from flask import render_template, redirect, request, url_for
from flask_login import (
    current_user,
    login_user,
    logout_user
)
from flask_dance.contrib.github import github
from apps import db, login_manager
from apps.authentication import blueprint
from apps.authentication.forms import LoginForm, CreateAccountForm
from apps.authentication.models import Users
from apps.authentication.util import verify_pass
from apps.authentication.models import AuctionItem
import pandas as pd
from io import BytesIO
from flask import Response

@blueprint.route('/show_auction_items')
# @login_required
def show_auction_items():
    auction_items = AuctionItem.query.limit(100).all()
    return render_template('home/auction_items.html', auction_items=auction_items, segment='show_auction_items')


from flask import jsonify

@blueprint.route('/live_search', methods=['POST'])
def live_search():
    search_term = request.json.get('search_term', '').strip()

    # Filter the data based on the search term
    if search_term:
        auction_items = AuctionItem.query.filter(AuctionItem.title.ilike(f"%{search_term}%")).limit(100).all()
    else:
        auction_items = AuctionItem.query.limit(100).all()

    # Convert the results to a format that can be sent as JSON
    items = [{"id": item.id, "title": item.title} for item in auction_items]  # Add other fields as needed

    return jsonify(auction_items=items)


from sqlalchemy import or_

@blueprint.route('/filterauction', methods=['GET', 'POST'])
# @login_required
def filterauction():
    # Fetch unique values for filters
    businesses = db.session.query(AuctionItem.business).distinct().all()
    bids = ["with", "without"]  # Manually defined
    reserves = [reserve[0] for reserve in db.session.query(AuctionItem.reserve).distinct().all()]
    auction_statuses = [status[0] for status in db.session.query(AuctionItem.status).distinct().all()]
    
    # Extract sort criteria from the request
    sort_column = request.args.get('sort_column', default='id')  # default to 'id' column if not provided
    sort_direction = request.args.get('sort_direction', default='asc')  # default to ascending if not provided
    
    # Extract search term from the request
    search_term = request.form.get('search_term', '').strip()
    
    if request.method == 'POST':
        # Get filter criteria from form
        business_filter = request.form.get('Business')
        reserve_filter = request.form.get('reserve')
        bids_filter = request.form.get('bids')
        status_filter = request.form.get('auctionStatus')
        
        # Create a query based on filter criteria
        query = AuctionItem.query
        if business_filter:
            query = query.filter(AuctionItem.business == business_filter)
        if reserve_filter:
            query = query.filter(AuctionItem.reserve == reserve_filter)
        if bids_filter:
            if bids_filter == 'with':
                query = query.filter(AuctionItem.bids > 0)
            else:
                query = query.filter(AuctionItem.bids == 0)
                
        if status_filter:
            query = query.filter(AuctionItem.status == status_filter)
            
        # Add sorting to the query
        if sort_direction == 'asc':
            query = query.order_by(getattr(AuctionItem, sort_column).asc())
        else:
            query = query.order_by(getattr(AuctionItem, sort_column).desc())
            
        # Add search term to the query
        # if search_term:
        #     query = query.filter(AuctionItem.title.ilike(f"%{search_term}%"))
        # For every field search term
        if search_term:
            search_filter = or_(
                AuctionItem.title.ilike(f"%{search_term}%"),
                AuctionItem.description.ilike(f"%{search_term}%"),
                AuctionItem.business.ilike(f"%{search_term}%"),
                AuctionItem.status.ilike(f"%{search_term}%"),
                # Add other fields as needed
            )
            query = query.filter(search_filter)
                
        # Execute the query
        auction_items = query.limit(100).all()
    else:
        # Default behavior when the page is loaded
        # if search_term:
        #     auction_items = AuctionItem.query.filter(AuctionItem.title.ilike(f"%{search_term}%")).order_by(getattr(AuctionItem, sort_column).send(sort_direction)()).limit(100).all()
        # for every field
        if search_term:
            search_filter = or_(
                AuctionItem.title.ilike(f"%{search_term}%"),
                AuctionItem.description.ilike(f"%{search_term}%"),
                AuctionItem.business.ilike(f"%{search_term}%"),
                AuctionItem.status.ilike(f"%{search_term}%"),
                # Add other fields as needed
            )
            auction_items = AuctionItem.query.filter(search_filter).order_by(getattr(AuctionItem, sort_column).send(sort_direction)()).limit(100).all()

        # auction_items = AuctionItem.query.limit(100).all()
        sorting_method = getattr(getattr(AuctionItem, sort_column), sort_direction)
        auction_items = AuctionItem.query.order_by(sorting_method()).limit(100).all()

    # return render_template('home/auction_items.html', auction_items=auction_items, segment='filterauction')
    return render_template(
        'home/auction_items.html', 
        auction_items=auction_items,
        businesses=businesses,
        reserves=reserves,
        bids=bids,
        auction_statuses=auction_statuses,
        segment='filterauction'
    )

@blueprint.route('/exportauction', methods=['POST'])
# @login_required
def exportauction():
    # Get filter criteria from form
    business_filter = request.form.get('Business')
    reserve_filter = request.form.get('reserve')
    bids_filter = request.form.get('bids')
    status_filter = request.form.get('auctionStatus')
    
    # Create a query based on filter criteria
    query = AuctionItem.query
    if business_filter:
        query = query.filter(AuctionItem.business == business_filter)
    if reserve_filter:
        query = query.filter(AuctionItem.reserve == reserve_filter)
    if bids_filter:
        if bids_filter == 'with':
            query = query.filter(AuctionItem.bids > 0)
        else:
            query = query.filter(AuctionItem.bids == 0)
    if status_filter:
        query = query.filter(AuctionItem.status == status_filter)
    
    # Execute the query
    auction_items = query.all()

    records = [item.to_dict() for item in auction_items]

    # Return the data as an Excel file
    if not records:
        return "No data to export", 400
    df = pd.DataFrame(records)
    output = BytesIO()  # Create an in-memory bytes buffer
    df.to_excel(output, index=False, engine='openpyxl')  # Write the DataFrame to the buffer
    output.seek(0)  # Go back to the start of the buffer

    response = Response(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response.headers["Content-Disposition"] = "attachment; filename=auction_data.xlsx"
    
    return response

@blueprint.route('/update_profile', methods=['POST'])
# @login_required
def update_profile():
    # Get data from form
    first_name = request.form.get('fn')
    last_name = request.form.get('ln')
    address = request.form.get('add')
    about_info = request.form.get('abt')

    # Update user in the database
    user = User.query.get(current_user.id)
    if user:
        user.first_name = first_name
        user.last_name = last_name
        user.address = address
        user.about_info = about_info
        db.session.commit()

    return redirect(url_for('profile_page_route')) # Redirect to the profile page after updating

@blueprint.route('/profile', methods=['GET', 'POST'])
# @login_required
def profile():
    if request.method == 'POST':
        # Handle profile updates here
        current_user.first_name = request.form.get('fn')
        current_user.last_name = request.form.get('ln')
        current_user.address = request.form.get('add')
        current_user.about = request.form.get('abt')
        db.session.commit()
        # Add a flash message or some notification that the profile was updated
        return redirect(url_for('authentication_blueprint.profile'))

    return render_template('home/profile.html', current_user=current_user)

@blueprint.route('/')
def route_default():
    return redirect(url_for('authentication_blueprint.login'))

# Login & Registration

@blueprint.route("/github")
def login_github():
    """ Github login """
    if not github.authorized:
        return redirect(url_for("github.login"))

    res = github.get("/user")
    return redirect(url_for('home_blueprint.index'))

@blueprint.route('/login', methods=['GET', 'POST'])
def login():
    login_form = LoginForm(request.form)
    if 'login' in request.form:

        # read form data
        user_id  = request.form['username'] # we can have here username OR email
        password = request.form['password']

        # Locate user
        user = Users.find_by_username(user_id)

        # if user not found
        if not user:

            user = Users.find_by_email(user_id)

            if not user:
                return render_template( 'accounts/login.html',
                                        msg='Unknown User or Email',
                                        form=login_form)

        # Check the password
        if verify_pass(password, user.password):

            login_user(user)
            return redirect(url_for('authentication_blueprint.route_default'))

        # Something (user or pass) is not ok
        return render_template('accounts/login.html',
                               msg='Wrong user or password',
                               form=login_form)

    if not current_user.is_authenticated:
        return render_template('accounts/login.html',
                               form=login_form)
    return redirect(url_for('home_blueprint.index'))


@blueprint.route('/register', methods=['GET', 'POST'])
def register():
    create_account_form = CreateAccountForm(request.form)
    if 'register' in request.form:

        username = request.form['username']
        email = request.form['email']

        # Check usename exists
        user = Users.query.filter_by(username=username).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Username already registered',
                                   success=False,
                                   form=create_account_form)

        # Check email exists
        user = Users.query.filter_by(email=email).first()
        if user:
            return render_template('accounts/register.html',
                                   msg='Email already registered',
                                   success=False,
                                   form=create_account_form)

        # else we can create the user
        user = Users(**request.form)
        db.session.add(user)
        db.session.commit()

        # Delete user from session
        logout_user()

        return render_template('accounts/register.html',
                               msg='User created successfully.',
                               success=True,
                               form=create_account_form)

    else:
        return render_template('accounts/register.html', form=create_account_form)


@blueprint.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('authentication_blueprint.login')) 

# Errors

@login_manager.unauthorized_handler
def unauthorized_handler():
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(403)
def access_forbidden(error):
    return render_template('home/page-403.html'), 403


@blueprint.errorhandler(404)
def not_found_error(error):
    return render_template('home/page-404.html'), 404


@blueprint.errorhandler(500)
def internal_error(error):
    return render_template('home/page-500.html'), 500
