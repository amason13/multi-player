"""Example usage of repository classes for Multi-Player Fantasy Football Platform.

This module demonstrates how to use the repository classes for common operations
in the Multi-Player fantasy football/tipping competition platform.
"""

from datetime import datetime, timedelta
import uuid
from .user import UserRepository
from .league import LeagueRepository
from .game import GameRepository
from .round import RoundRepository
from .prediction import PredictionRepository
from .standings import StandingsRepository
from .invitation import InvitationRepository
from .table import DynamoDBTable


def example_user_operations():
    """Example: User profile and statistics operations."""
    print("\n=== USER OPERATIONS ===")
    
    user_repo = UserRepository()
    user_id = str(uuid.uuid4())
    
    # Get user profile
    profile = user_repo.get_profile(user_id)
    print(f"User profile: {profile}")
    
    # Update user profile
    updated = user_repo.update_profile(user_id, {
        'name': 'John Doe',
        'timezone': 'America/New_York'
    })
    print(f"Updated profile: {updated}")
    
    # Get user statistics
    stats = user_repo.get_statistics(user_id, 'league-001')
    print(f"User stats: {stats}")
    
    # Get all user leagues
    leagues = user_repo.get_user_data(user_id)
    print(f"User data: {leagues}")


def example_league_operations():
    """Example: League creation and member management."""
    print("\n=== LEAGUE OPERATIONS ===")
    
    league_repo = LeagueRepository()
    league_id = str(uuid.uuid4())
    owner_id = str(uuid.uuid4())
    
    # Create league
    league = league_repo.create_league(
        league_id=league_id,
        name='Premier League 2024-25',
        owner_id=owner_id,
        description='Official Premier League competition'
    )
    print(f"Created league: {league}")
    
    # Get league details
    league_details = league_repo.get_league(league_id)
    print(f"League details: {league_details}")
    
    # Add members
    member1_id = str(uuid.uuid4())
    member2_id = str(uuid.uuid4())
    
    league_repo.add_member(league_id, member1_id, 'ADMIN')
    league_repo.add_member(league_id, member2_id, 'MEMBER')
    print(f"Added members to league")
    
    # Get league members
    members = league_repo.get_members(league_id)
    print(f"League members: {len(members)}")
    
    # Check membership
    is_member = league_repo.is_member(league_id, member1_id)
    print(f"Is member: {is_member}")
    
    # Get user's leagues
    user_leagues = league_repo.get_user_leagues(owner_id)
    print(f"User's leagues: {len(user_leagues)}")


def example_game_operations():
    """Example: Game creation and member management."""
    print("\n=== GAME OPERATIONS ===")
    
    game_repo = GameRepository()
    league_id = str(uuid.uuid4())
    game_id = str(uuid.uuid4())
    
    # Create game
    game = game_repo.create_game(
        game_id=game_id,
        league_id=league_id,
        game_type='POINTS_BASED',
        name='Week 1 Predictions'
    )
    print(f"Created game: {game}")
    
    # Get game details
    game_details = game_repo.get_game(game_id)
    print(f"Game details: {game_details}")
    
    # Add members
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    
    game_repo.add_member(game_id, user1_id)
    game_repo.add_member(game_id, user2_id)
    print(f"Added members to game")
    
    # Get game members
    members = game_repo.get_members(game_id)
    print(f"Game members: {len(members)}")
    
    # LMS-specific: Eliminate member
    game_repo.eliminate_member(game_id, user1_id, round_number=1)
    print(f"Eliminated member from LMS game")
    
    # Check elimination status
    is_eliminated = game_repo.is_eliminated(game_id, user1_id)
    print(f"Is eliminated: {is_eliminated}")


def example_round_operations():
    """Example: Round creation and match management."""
    print("\n=== ROUND OPERATIONS ===")
    
    round_repo = RoundRepository()
    league_id = str(uuid.uuid4())
    game_id = str(uuid.uuid4())
    round_id = str(uuid.uuid4())
    
    # Create round
    round_item = round_repo.create_round(
        round_id=round_id,
        league_id=league_id,
        game_id=game_id,
        round_number=1,
        game_type='POINTS_BASED',
        start_date=datetime.utcnow().isoformat(),
        prediction_deadline=(datetime.utcnow() + timedelta(days=7)).isoformat()
    )
    print(f"Created round: {round_item}")
    
    # Get round details
    round_details = round_repo.get_round(league_id, 1)
    print(f"Round details: {round_details}")
    
    # Add matches
    match1_id = str(uuid.uuid4())
    match2_id = str(uuid.uuid4())
    
    round_repo.add_match(
        league_id=league_id,
        round_number=1,
        match_id=match1_id,
        home_team='Manchester United',
        away_team='Liverpool',
        match_date=datetime.utcnow().isoformat()
    )
    round_repo.add_match(
        league_id=league_id,
        round_number=1,
        match_id=match2_id,
        home_team='Arsenal',
        away_team='Chelsea',
        match_date=datetime.utcnow().isoformat()
    )
    print(f"Added matches to round")
    
    # Get matches
    matches = round_repo.get_matches(league_id, 1)
    print(f"Round matches: {len(matches)}")
    
    # Set match result
    round_repo.set_match_result(league_id, 1, match1_id, home_score=2, away_score=1)
    print(f"Set match result")
    
    # Update round status
    round_repo.update_round_status(league_id, 1, 'COMPLETED')
    print(f"Updated round status to COMPLETED")


def example_prediction_operations():
    """Example: Prediction submission and scoring."""
    print("\n=== PREDICTION OPERATIONS ===")
    
    pred_repo = PredictionRepository()
    user_id = str(uuid.uuid4())
    league_id = str(uuid.uuid4())
    match_id = str(uuid.uuid4())
    
    # Submit points-based prediction
    pred_id = str(uuid.uuid4())
    prediction = pred_repo.submit_points_based_prediction(
        prediction_id=pred_id,
        user_id=user_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        predicted_home_score=2,
        predicted_away_score=1,
        confidence_level=8,
        reasoning='Strong home form'
    )
    print(f"Submitted prediction: {prediction}")
    
    # Get user's predictions for round
    predictions = pred_repo.get_user_predictions_for_round(user_id, league_id, 1)
    print(f"User predictions for round: {len(predictions)}")
    
    # Score prediction
    scored = pred_repo.score_points_based_prediction(
        user_id=user_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        actual_home_score=2,
        actual_away_score=1,
        points_earned=10
    )
    print(f"Scored prediction: {scored}")
    
    # Submit LMS prediction
    lms_pred_id = str(uuid.uuid4())
    lms_prediction = pred_repo.submit_lms_prediction(
        prediction_id=lms_pred_id,
        user_id=user_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        predicted_winner='HOME',
        confidence_level=7
    )
    print(f"Submitted LMS prediction: {lms_prediction}")


def example_standings_operations():
    """Example: Standings computation and retrieval."""
    print("\n=== STANDINGS OPERATIONS ===")
    
    standings_repo = StandingsRepository()
    league_id = str(uuid.uuid4())
    game_id = str(uuid.uuid4())
    
    # Create standings data
    standings_data = [
        {
            'rank': 1,
            'user_id': str(uuid.uuid4()),
            'user_name': 'John Doe',
            'total_points': 100,
            'games_played': 1,
            'correct_predictions': 10,
            'total_predictions': 10,
            'prediction_accuracy': 100.0
        },
        {
            'rank': 2,
            'user_id': str(uuid.uuid4()),
            'user_name': 'Jane Smith',
            'total_points': 85,
            'games_played': 1,
            'correct_predictions': 8,
            'total_predictions': 10,
            'prediction_accuracy': 80.0
        }
    ]
    
    # Create standings
    standings = standings_repo.create_standings(
        standings_id=str(uuid.uuid4()),
        league_id=league_id,
        game_id=game_id,
        game_type='POINTS_BASED',
        round_number=1,
        standings_data=standings_data
    )
    print(f"Created standings: {standings}")
    
    # Get standings
    standings_details = standings_repo.get_standings(league_id, 'POINTS_BASED', 1)
    print(f"Standings details: {standings_details}")
    
    # Get top players
    top_players = standings_repo.get_top_players(league_id, 'POINTS_BASED', 1, limit=5)
    print(f"Top players: {len(top_players)}")
    
    # Get user's rank
    user_id = standings_data[0]['user_id']
    rank = standings_repo.get_user_rank(league_id, 'POINTS_BASED', 1, user_id)
    print(f"User rank: {rank}")
    
    # Lock standings
    standings_repo.lock_standings(league_id, 'POINTS_BASED', 1, 'admin-user-id')
    print(f"Locked standings")


def example_invitation_operations():
    """Example: League invitation management."""
    print("\n=== INVITATION OPERATIONS ===")
    
    inv_repo = InvitationRepository()
    league_id = str(uuid.uuid4())
    inviter_id = str(uuid.uuid4())
    invitee_id = str(uuid.uuid4())
    
    # Send invitation
    inv_id = str(uuid.uuid4())
    invitation = inv_repo.create_invitation(
        invitation_id=inv_id,
        league_id=league_id,
        inviter_id=inviter_id,
        invitee_email='user@example.com',
        invitee_id=invitee_id
    )
    print(f"Created invitation: {invitation}")
    
    # Get pending invitations
    pending = inv_repo.get_pending_invitations(invitee_id)
    print(f"Pending invitations: {len(pending)}")
    
    # Accept invitation
    accepted = inv_repo.accept_invitation(inv_id, invitee_id)
    print(f"Accepted invitation: {accepted}")
    
    # Send bulk invitations
    emails = ['user1@example.com', 'user2@example.com', 'user3@example.com']
    bulk_invitations = inv_repo.send_bulk_invitations(league_id, inviter_id, emails)
    print(f"Sent {len(bulk_invitations)} bulk invitations")


def example_complete_workflow():
    """Example: Complete workflow from league creation to standings."""
    print("\n=== COMPLETE WORKFLOW ===")
    
    # Initialize repositories
    league_repo = LeagueRepository()
    game_repo = GameRepository()
    round_repo = RoundRepository()
    pred_repo = PredictionRepository()
    standings_repo = StandingsRepository()
    
    # 1. Create league
    league_id = str(uuid.uuid4())
    owner_id = str(uuid.uuid4())
    league = league_repo.create_league(
        league_id=league_id,
        name='Fantasy Football League',
        owner_id=owner_id
    )
    print(f"1. Created league: {league['league_id']}")
    
    # 2. Add members
    user1_id = str(uuid.uuid4())
    user2_id = str(uuid.uuid4())
    league_repo.add_member(league_id, user1_id)
    league_repo.add_member(league_id, user2_id)
    print(f"2. Added 2 members to league")
    
    # 3. Create game
    game_id = str(uuid.uuid4())
    game = game_repo.create_game(
        game_id=game_id,
        league_id=league_id,
        game_type='POINTS_BASED'
    )
    game_repo.add_member(game_id, user1_id)
    game_repo.add_member(game_id, user2_id)
    print(f"3. Created game with 2 members")
    
    # 4. Create round with matches
    round_id = str(uuid.uuid4())
    round_item = round_repo.create_round(
        round_id=round_id,
        league_id=league_id,
        game_id=game_id,
        round_number=1,
        game_type='POINTS_BASED'
    )
    match_id = str(uuid.uuid4())
    round_repo.add_match(
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        home_team='Team A',
        away_team='Team B'
    )
    print(f"4. Created round with 1 match")
    
    # 5. Submit predictions
    pred1_id = str(uuid.uuid4())
    pred_repo.submit_points_based_prediction(
        prediction_id=pred1_id,
        user_id=user1_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        predicted_home_score=2,
        predicted_away_score=1
    )
    pred2_id = str(uuid.uuid4())
    pred_repo.submit_points_based_prediction(
        prediction_id=pred2_id,
        user_id=user2_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        predicted_home_score=1,
        predicted_away_score=1
    )
    print(f"5. Submitted 2 predictions")
    
    # 6. Set match result and score predictions
    round_repo.set_match_result(league_id, 1, match_id, 2, 1)
    pred_repo.score_points_based_prediction(
        user_id=user1_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        actual_home_score=2,
        actual_away_score=1,
        points_earned=10
    )
    pred_repo.score_points_based_prediction(
        user_id=user2_id,
        league_id=league_id,
        round_number=1,
        match_id=match_id,
        actual_home_score=2,
        actual_away_score=1,
        points_earned=5
    )
    print(f"6. Scored predictions")
    
    # 7. Compute standings
    predictions = [
        {'user_id': user1_id, 'user_name': 'User 1', 'points_earned': 10, 'accuracy_type': 'EXACT_SCORE'},
        {'user_id': user2_id, 'user_name': 'User 2', 'points_earned': 5, 'accuracy_type': 'CORRECT_RESULT'}
    ]
    standings = standings_repo.compute_points_based_standings(
        league_id=league_id,
        game_id=game_id,
        round_number=1,
        predictions=predictions
    )
    print(f"7. Computed standings")
    
    print(f"\nWorkflow complete! League {league_id} is ready for competition.")


if __name__ == '__main__':
    print("Multi-Player Fantasy Football Repository Examples")
    print("=" * 50)
    
    # Run examples
    example_user_operations()
    example_league_operations()
    example_game_operations()
    example_round_operations()
    example_prediction_operations()
    example_standings_operations()
    example_invitation_operations()
    example_complete_workflow()
    
    print("\n" + "=" * 50)
    print("Examples completed!")
