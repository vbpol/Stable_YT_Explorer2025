from sqlalchemy.orm import sessionmaker
from sqlalchemy import create_engine

def get_session(database_url='sqlite:///youtube.db'):
    """Create and return a new SQLAlchemy session."""
    engine = create_engine(database_url)
    Session = sessionmaker(bind=engine)
    return Session()

def update_is_downloaded(entity, session, is_downloaded=True):
    """
    Update the is_downloaded field for a playlist or video in the database.
    :param entity: The playlist or video object to update
    :param session: The SQLAlchemy session
    :param is_downloaded: Boolean indicating whether the entity is downloaded
    """
    try:
        entity.is_downloaded = is_downloaded
        session.commit()
        print(f"Updated is_downloaded for {entity.__class__.__name__} with ID: {entity.id}")
    except Exception as e:
        session.rollback()
        print(f"Failed to update is_downloaded: {e}")
