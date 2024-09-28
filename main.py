from fastapi import FastAPI, HTTPException, status, Header
from database import database, post_table, user_table
from models.post import UserPost, UserPostIn  
from models.user import UserIn
from security import get_password_hash, create_access_token, authenticate_user
from fastapi import Depends
from models.user import User
from security import get_current_user
from models.post import Comment, CommentIn
from database import comments_table
from models.post import UserPostWithComments

app = FastAPI()  

@app.on_event("startup")
async def startup():
    await database.connect()

@app.on_event("shutdown")
async def shutdown():
    await database.disconnect()

@app.post("/register")
async def register(user: UserIn):
    hashed_password = get_password_hash(user.password)
    query = user_table.insert().values(username=user.username, password=hashed_password)
    await database.execute(query)
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.post("/token")
async def login(user: UserIn):
    user = await authenticate_user(user.username, user.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    access_token = create_access_token(user.username)
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=User)
async def read_users_me(current_user: User = Depends(get_current_user)):
    return current_user

@app.post("/post", response_model=UserPost)
async def create_post(
    post: UserPostIn, current_user: User = Depends(get_current_user)
):
    data = {**post.dict(), "user_id": current_user.id}
    query = post_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}

@app.post("/post", response_model=UserPost)  
async def create_post(post: UserPostIn):  
    query = post_table.insert().values(name=post.name, body=post.body)  
    post_id = await database.execute(query)  
    return {**post.model_dump(), "id": post_id}  # Using model_dump instead of dict()  

@app.get("/posts", response_model=list[UserPost])  
async def get_all_posts():  
    query = post_table.select()
    results = await database.fetch_all(query)
    return [UserPost(**result).model_dump() for result in results]  # Using model_dump on individual instances

@app.post("/comment", response_model=Comment)
async def create_comment(
    comment: CommentIn, current_user: User = Depends(get_current_user)
):
    data = {**comment.dict(), "user_id": current_user.id}
    query = comments_table.insert().values(data)
    last_record_id = await database.execute(query)
    return {**data, "id": last_record_id}

@app.get("/post/{post_id}/comments", response_model=list[Comment])
async def get_comments_on_post(post_id: int):
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    return await database.fetch_all(query)

@app.get("/posts/{post_id}", response_model=UserPostWithComments)
async def get_post_with_comments(post_id: int):
    query = post_table.select().where(post_table.c.id == post_id)
    post = await database.fetch_one(query)
    query = comments_table.select().where(comments_table.c.post_id == post_id)
    comments = await database.fetch_all(query)
    return {**post, "comments": comments}

# Let’s break down both lines of code and explain them in detail with examples.

# ### 1. Line: `return {**post.model_dump(), "id": post_id}`

# #### Explanation
# - This line returns a dictionary that combines the properties of the `post` object (represented by `post.model_dump()`) with a new key-value pair for the `"id"` of the post.

# #### Components
# - **`post.model_dump()`**: This method is presumably part of a Pydantic model. It returns a dictionary representation of the `post` object, including all its attributes. 
# - **`post_id`**: This is a variable expected to hold the ID of the newly created post (e.g., retrieved from the database when inserting a new record).

# #### Example
# Suppose we have a Pydantic model for a post defined as follows:

# ```python
# from pydantic import BaseModel

# class UserPostIn(BaseModel):
#     name: str
#     body: str

# post = UserPostIn(name="My First Post", body="This is the content of my first post.")
# post_id = 1  # Let's say this is the ID returned by the database after insertion.
# ```

# When we call `post.model_dump()`:
# ```python
# post_dict = post.model_dump()
# ```
# This would result in:
# ```python
# {'name': 'My First Post', 'body': 'This is the content of my first post.'}
# ```

# Now when we execute:
# ```python
# return {**post.model_dump(), "id": post_id}
# ```
# It combines `post_dict` with `post_id`:
# ```python
# {
#     'name': 'My First Post',
#     'body': 'This is the content of my first post.',
#     'id': 1
# }
# ```
# This resulting dictionary is returned from the function, which essentially confirms the creation of the post with the given ID.

# ### 2. Line: `return [UserPost(**result).model_dump() for result in results]`

# #### Explanation
# - This line returns a list of dictionaries, with each dictionary representing a `UserPost` object created from the data in `results`. It uses a list comprehension to achieve this.

# #### Components
# - **`results`**: This is expected to be a list of dictionaries (often rows fetched from a database) where each dictionary contains the fields corresponding to the `UserPost` model.
# - **`UserPost(**result)`**: This instantiates a `UserPost` object using unpacking (`**`), allowing the dictionary values to be passed as keyword arguments.
# - **`.model_dump()`**: This method converts the `UserPost` instance back into a dictionary.

# #### Example
# Assuming that we have the following `results` retrieved from a database query:

# ```python
# results = [
#     {'id': 1, 'name': 'My First Post', 'body': 'This is the content of my first post.'},
#     {'id': 2, 'name': 'My Second Post', 'body': 'This is the content of my second post.'}
# ]
# ```

# The comprehension:
# ```python
# return [UserPost(**result).model_dump() for result in results]
# ```
# Would go through each dictionary in `results`:

# 1. For the first `result`:
#    - **Creating the object**: `UserPost(**result)` translates to `UserPost(id=1, name='My First Post', body='This is the content of my first post.')`.
#    - **Converting back to dictionary**: The `model_dump()` would return:
#    ```python
#    {'id': 1, 'name': 'My First Post', 'body': 'This is the content of my first post.'}
#    ```

# 2. For the second `result`:
#    - **Creating the object**: `UserPost(**result)` translates to `UserPost(id=2, name='My Second Post', body='This is the content of my second post.')`.
#    - **Converting back to dictionary**: The `model_dump()` would return:
#    ```python
#    {'id': 2, 'name': 'My Second Post', 'body': 'This is the content of my second post.'}
#    ```

# After the list comprehension finishes, the result would be:
# ```python
# [
#     {'id': 1, 'name': 'My First Post', 'body': 'This is the content of my first post.'},
#     {'id': 2, 'name': 'My Second Post', 'body': 'This is the content of my second post.'}
# ]
# ```

# ### Summary

# To summarize:
# - The first line returns a single post’s data as a dictionary, including its ID after insertion.
# - The second line processes multiple post records and returns a list of their data as dictionaries. 

# Both lines leverage the capabilities of Pydantic models to ensure consistent data structure and validation in the application.
