#!/binb/bash


## GIT_AUTHOR_NAME is the human-readable name in the “author” field.
## 
## GIT_AUTHOR_EMAIL is the email for the “author” field.
## 
## GIT_AUTHOR_DATE is the timestamp used for the “author” field.
## 
## GIT_COMMITTER_NAME sets the human name for the “committer” field.
## 
## GIT_COMMITTER_EMAIL is the email address for the “committer” field.
## 
## GIT_COMMITTER_DATE is used for the timestamp in the “committer” field.


export GIT_AUTHOR_NAME="Naoto Gokho"
export GIT_AUTHOR_EMAIL="naoto-gohko@gmo.jp"

export GIT_COMMITTER_NAME=$GIT_AUTHOR_NAME
export GIT_COMMITTER_EMAIL=$GIT_AUTHOR_EMAIL


