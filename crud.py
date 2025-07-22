

#Demarche pour l ajout de tout les entites 
from utils.db import get_db_connection
from utils.hash import hash_password,verify_password


def add_Apprenants(nom:str,password:str):
    conn=get_db_connection()
    cursor=conn.cursor()
    hash_pwd=hash_password(password)
    
    cursor.execute("""
    INSERT INTO Apprenants (
        Nom, Prenom, AdresseEmail, MotDePasse, Phone,
        Ville, TypeDeFormation, CodeCoupon,
        DateDebutFormation, DateFinFormation, Centre, NiveauDeConnaissance
    ) VALUES (
        %s, %s, %s, %s, %s,
        %s, %s, %s,
        %s, %s, %s, %s
    )
""", (
    "Doe", "John", nom+"@gmail.com", hash_pwd, "0612345678",
    "Casablanca", "Développement Web", "COUPON123",
    "2025-08-01", "2025-10-01", "Centre Casablanca", "Débutant"
))
    conn.commit()
    conn.close()


def verify_user(email:str,password:str):
    conn=get_db_connection()
    cursor=conn.cursor(dictionary=True)
    cursor.execute("""
                   select * from Apprenants where AdresseEmail=%s
                   """,(email,))
    user = cursor.fetchone()
    print(user)
    if verify_password(user['MotDePasse'],password):
        print("Password Matches")





verify_user("karim@gmail.com","202020")