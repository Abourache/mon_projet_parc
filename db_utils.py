from db_config import get_connection
from datetime import datetime

# ============================================
# Query Functions (SELECT)
# ============================================


def get_all_ordinateurs():
    """Get all computers"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*, 
                       CONCAT(e.Prenom, ' ', e.Nom) AS employe_actuel
                FROM ordinateur o
                LEFT JOIN affectation a ON o.Id_Ordinateur = a.Id_Ordinateur 
                    AND a.Date_Restitution IS NULL
                LEFT JOIN employe e ON a.Matricule = e.Matricule
                ORDER BY o.Id_Ordinateur
            """)
            return cursor.fetchall()
    finally:
        conn.close()


def search_ordinateurs(search_text):
    """Search computers and employees by id or name using a single keyword."""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            search_value = f"%{search_text}%"
            cursor.execute("""
                SELECT o.*, 
                       CONCAT(e.Prenom, ' ', e.Nom) AS employe_actuel
                FROM ordinateur o
                LEFT JOIN affectation a ON o.Id_Ordinateur = a.Id_Ordinateur 
                    AND a.Date_Restitution IS NULL
                LEFT JOIN employe e ON a.Matricule = e.Matricule
                WHERE o.Num_Inventaire LIKE %s
                   OR o.Num_Serie LIKE %s
                   OR o.Marque LIKE %s
                   OR o.Modele LIKE %s
                   OR e.Matricule LIKE %s
                   OR e.Nom LIKE %s
                   OR e.Prenom LIKE %s
                ORDER BY o.Id_Ordinateur
            """, (search_value, search_value, search_value, search_value,
                  search_value, search_value, search_value))
            return cursor.fetchall()
    finally:
        conn.close()


def get_ordinateur_by_inventaire(num_inventaire):
    """Get a computer by inventory number"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM ordinateur WHERE Num_Inventaire = %s",
                (num_inventaire,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def get_employes_actifs():
    """Get only active employees"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM employe WHERE Statut = 'Actif' ORDER BY Nom"
            )
            return cursor.fetchall()
    finally:
        conn.close()


def get_affectations_by_ordinateur(ordinateur_id):
    """Get movement history of a specific computer"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT a.*, 
                       CONCAT(e.Prenom, ' ', e.Nom) AS employe_nom
                FROM affectation a
                JOIN employe e ON a.Matricule = e.Matricule
                WHERE a.Id_Ordinateur = %s
                ORDER BY a.Date_Affectation DESC
            """, (ordinateur_id,))
            return cursor.fetchall()
    finally:
        conn.close()


def get_ordinateurs_a_remplacer():
    """Get computers that are 5 years old or older"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT *, 
                       DATEDIFF(CURDATE(), Date_Mise_Service) DIV 365 AS annees_ecoulees
                FROM ordinateur
                WHERE DATEDIFF(CURDATE(), Date_Mise_Service) >= 5 * 365
                ORDER BY Date_Mise_Service
            """)
            return cursor.fetchall()
    finally:
        conn.close()


def get_ordinateurs_disponibles():
    """Get currently unassigned computers (available for handover)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                SELECT o.*
                FROM ordinateur o
                WHERE o.Etat != 'Hors service'
                  AND o.Id_Ordinateur NOT IN (
                      SELECT Id_Ordinateur 
                      FROM affectation 
                      WHERE Date_Restitution IS NULL
                  )
                ORDER BY o.Num_Inventaire
            """)
            return cursor.fetchall()
    finally:
        conn.close()

# ============================================
# Insert Functions (INSERT)
# ============================================


def ajouter_ordinateur(data):
    """
    Add a new computer
    data: dict containing keys:
        Num_Inventaire, Num_Serie, Brand, Model, 
        Date_Achat, Date_Mise_Service, Status, Id_Achat (optional)
    """
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO ordinateur 
                (Num_Inventaire, Num_Serie, Marque, Modele, 
                 Date_Achat, Date_Mise_Service, Etat, Id_Achat)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['Num_Inventaire'],
                data['Num_Serie'],
                data.get('Marque'),
                data.get('Modele'),
                data.get('Date_Achat'),
                data['Date_Mise_Service'],
                data.get('Etat', 'Neuf'),
                data.get('Id_Achat')
            ))
            conn.commit()
            return cursor.lastrowid  # Return new computer ID
    finally:
        conn.close()


def ajouter_employe(data):
    """Add a new employee"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            sql = """
                INSERT INTO employe (Matricule, Nom, Prenom, Service, Poste, Statut)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(sql, (
                data['Matricule'],
                data['Nom'],
                data['Prenom'],
                data.get('Service'),
                data.get('Poste'),
                data.get('Statut', 'Actif')
            ))
            conn.commit()
            return True
    finally:
        conn.close()


def affecter_ordinateur(ordinateur_id, matricule, date_affectation):
    """Hand over computer to employee"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Check: Is the computer currently assigned to another employee?
            cursor.execute("""
                SELECT * FROM affectation 
                WHERE Id_Ordinateur = %s AND Date_Restitution IS NULL
            """, (ordinateur_id,))
            if cursor.fetchone():
                raise Exception(
                    "This computer is currently assigned to another employee!")

            # Add new assignment
            cursor.execute("""
                INSERT INTO affectation (Id_Ordinateur, Matricule, Date_Affectation)
                VALUES (%s, %s, %s)
            """, (ordinateur_id, matricule, date_affectation))

            # Update computer status to "In Service"
            cursor.execute("""
                UPDATE ordinateur SET Etat = 'En service' 
                WHERE Id_Ordinateur = %s
            """, (ordinateur_id,))

            conn.commit()
            return True
    finally:
        conn.close()


def restituer_ordinateur(ordinateur_id, date_restitution):
    """Return a computer from an employee"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Find the active assignment
            cursor.execute("""
                SELECT Id_Affectation FROM affectation
                WHERE Id_Ordinateur = %s AND Date_Restitution IS NULL
            """, (ordinateur_id,))
            affectation = cursor.fetchone()

            if not affectation:
                raise Exception(
                    "This computer is not assigned to any employee!")

            # Update return date
            cursor.execute("""
                UPDATE affectation 
                SET Date_Restitution = %s
                WHERE Id_Affectation = %s
            """, (date_restitution, affectation['Id_Affectation']))

            # Update computer status to "New"
            cursor.execute("""
                UPDATE ordinateur SET Etat = 'Neuf' 
                WHERE Id_Ordinateur = %s
            """, (ordinateur_id,))

            conn.commit()
            return True
    finally:
        conn.close()

# ============================================
# Update Functions (UPDATE)
# ============================================


def update_etat_ordinateur(ordinateur_id, nouvel_etat):
    """Update computer status"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute("""
                UPDATE ordinateur 
                SET Etat = %s 
                WHERE Id_Ordinateur = %s
            """, (nouvel_etat, ordinateur_id))
            conn.commit()
            return True
    finally:
        conn.close()

# ============================================
# Delete Functions (DELETE) - With Caution!
# ============================================


def supprimer_ordinateur(ordinateur_id):
    """Delete a computer (requires deleting related assignments first)"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Delete related assignments
            cursor.execute(
                "DELETE FROM affectation WHERE Id_Ordinateur = %s",
                (ordinateur_id,)
            )
            # Delete the computer
            cursor.execute(
                "DELETE FROM ordinateur WHERE Id_Ordinateur = %s",
                (ordinateur_id,)
            )
            conn.commit()
            return True
    finally:
        conn.close()

# Add to db_utils.py


def get_ordinateur_by_inventaire(num_inventaire):
    """Get a computer by inventory number"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            cursor.execute(
                "SELECT * FROM ordinateur WHERE Num_Inventaire = %s",
                (num_inventaire,)
            )
            return cursor.fetchone()
    finally:
        conn.close()


def restituer_ordinateur_by_inventaire(num_inventaire, date_restitution):
    """Return a computer by inventory number"""
    conn = get_connection()
    try:
        with conn.cursor() as cursor:
            # Find the active assignment
            cursor.execute("""
                SELECT a.Id_Affectation, a.Id_Ordinateur
                FROM affectation a
                JOIN ordinateur o ON a.Id_Ordinateur = o.Id_Ordinateur
                WHERE o.Num_Inventaire = %s AND a.Date_Restitution IS NULL
            """, (num_inventaire,))

            affectation = cursor.fetchone()
            if not affectation:
                raise Exception("This computer is not assigned to anyone!")

            # Update restitution date
            cursor.execute("""
                UPDATE affectation 
                SET Date_Restitution = %s
                WHERE Id_Affectation = %s
            """, (date_restitution, affectation['Id_Affectation']))

            # Update computer status
            cursor.execute("""
                UPDATE ordinateur SET Etat = 'Neuf'
                WHERE Id_Ordinateur = %s
            """, (affectation['Id_Ordinateur'],))

            conn.commit()
            return True
    finally:
        conn.close()
