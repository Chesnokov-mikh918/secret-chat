from auth.schemas import Base

class CreateDirectIn(Base):
    user_id: int

class GroupChatIn(Base):
    creator_id: int
    users_id : List[int]