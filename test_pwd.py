from passlib.context import CryptContext

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
hashed = "$2b$12$jJeBKka.QqUKZSFdCY7iIO42.ZTtETEBotz0/.aLIv.VAJRhbdaFO"
password = "Dbpfs2001$dbpfs2001"

print(pwd_context.verify(password, hashed))
