

from flask import Flask, render_template, request, redirect, url_for, flash
from db_utils import *
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your-secret-key-here-change-it'

# ============================================
# Homepage - List all computers
# ============================================


@app.route('/')
def index():
    search = request.args.get('q', '').strip()

    if search:
        ordinateurs = search_ordinateurs(search)
    else:
        ordinateurs = get_all_ordinateurs()

    return render_template('index.html', ordinateurs=ordinateurs, search=search)

# ============================================
# Add Computer
# ============================================


@app.route('/ajouter_ordinateur', methods=['GET', 'POST'])
def ajouter_ordinateur_route():
    if request.method == 'POST':
        data = {
            'Num_Inventaire': request.form['num_inventaire'],
            'Num_Serie': request.form['num_serie'],
            'Marque': request.form['marque'],
            'Modele': request.form['modele'],
            'Date_Achat': request.form['date_achat'] or None,
            'Date_Mise_Service': request.form['date_mise_service'],
            'Etat': request.form['etat']
        }
        try:
            ajouter_ordinateur(data)  # ← Calls db_utils function
            flash('✅ Computer added successfully!', 'success')
            return redirect(url_for('index'))  # ← Go back to homepage
        except Exception as e:
            flash(f'❌ Error: {e}', 'error')
            return redirect(url_for('ajouter_ordinateur_route'))

    return render_template('ajouter_ordinateur.html')

# ============================================
# Assign Computer
# ============================================


@app.route('/affecter', methods=['GET', 'POST'])
def affecter():
    if request.method == 'POST':
        ordinateur_id = request.form['ordinateur_id']
        matricule = request.form['matricule']
        date_affectation = request.form['date_affectation']

        try:
            affecter_ordinateur(int(ordinateur_id),
                                matricule, date_affectation)
            flash('✅ Computer assigned successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Error: {e}', 'error')
            return redirect(url_for('affecter'))

    ordinateurs_disponibles = get_ordinateurs_disponibles()
    employes_actifs = get_employes_actifs()
    return render_template('affecter.html',
                           ordinateurs=ordinateurs_disponibles,
                           employes=employes_actifs)

# ============================================
# Return Computer
# ============================================


@app.route('/restituer', methods=['GET', 'POST'])
def restituer():
    if request.method == 'POST':
        num_inventaire = request.form['num_inventaire']
        date_restitution = request.form['date_restitution']

        try:
            restituer_ordinateur_by_inventaire(
                num_inventaire, date_restitution)
            flash('✅ Computer returned successfully!', 'success')
            return redirect(url_for('index'))
        except Exception as e:
            flash(f'❌ Error: {e}', 'error')
            return redirect(url_for('restituer'))

    ordinateurs = get_all_ordinateurs()

    return render_template('restituer.html', ordinateurs=ordinateurs)

# ============================================
# Reports
# ============================================


@app.route('/rapports')
def rapports():
    a_remplacer = get_ordinateurs_a_remplacer()
    return render_template('rapports.html', a_remplacer=a_remplacer)


# ============================================
# Run the application
# ============================================
if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=5000)
