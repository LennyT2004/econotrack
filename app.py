from flask import Flask, render_template, request, session, redirect, url_for, Response, flash
from flask_session import Session
from firebase import auth, db, login, signup, get_user_data, update_user_data
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
import io

app = Flask(__name__)

# Configuration Flask
app.config["SESSION_TYPE"] = "filesystem"
app.secret_key = "94b1025132cce2e19cb43f4e8ea51de8b6871ab6480ff5db"
Session(app)

# Protection des routes nécessitant une connexion
def login_required(f):
    def wrapper(*args, **kwargs):
        if "user" not in session:
            return redirect(url_for("auth_page"))
        return f(*args, **kwargs)
    return wrapper

# Variables pour le total des dépenses et revenus
total_depenses = 0
total_revenus = 0

@app.route("/", methods=["GET", "POST"])
@login_required
def index():
    global total_depenses, total_revenus # Définition des variables en global pour les rendre accessible de partout

    # Nécessité d'être connecté pour accéder à la page
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("auth_page"))

    # Récupération des données des utilisateurs
    user_data = get_user_data(uid)
    session["expenses"] = user_data.get("expenses", [])
    session["revenus"] = user_data.get("revenus", [])
    session["budget"] = user_data.get("budget", 0)
    session["budget_expenses"] = user_data.get("budget_expenses", [])

    # Gestion des formulaires et récupération des données saisies
    if request.method == "POST":
        form_type = request.form.get("form_type")

        # Si le formulaire est celui des dépenses
        if form_type == "form_expenses":
            description = request.form.get("description_expenses")
            amount = request.form.get("amount_expenses")
            if description and amount:
                try:
                    amount = float(amount)
                    session["expenses"].append({"description": description, "amount": amount})
                    update_user_data(uid, {
                        "expenses": session["expenses"],
                        "revenus": session["revenus"],
                        "budget": session["budget"],
                        "budget_expenses": session["budget_expenses"]
                    })
                    return redirect("/")
                except ValueError:
                    pass
        # Si le formulaire est celui des revenus
        elif form_type == "form_revenus":
            description = request.form.get("description_revenus")
            amount = request.form.get("amount_revenus")
            if description and amount:
                try:
                    amount = float(amount)
                    session["revenus"].append({"description": description, "amount": amount})
                    update_user_data(uid, {
                        "expenses": session["expenses"],
                        "revenus": session["revenus"],
                        "budget": session["budget"],
                        "budget_expenses": session["budget_expenses"]
                    })
                    return redirect("/")
                except ValueError:
                    pass
        # Si le formulaire est celui du budget
        elif form_type == "set_budget":
            budget = request.form.get("budget")
            if budget:
                try:
                    session["budget"] = float(budget)
                    session["budget_expenses"] = []
                    update_user_data(uid, {
                        "expenses": session["expenses"],
                        "revenus": session["revenus"],
                        "budget": session["budget"],
                        "budget_expenses": session["budget_expenses"]
                    })
                    return redirect("/")
                except ValueError:
                    pass
        # Si le formulaire est celui des dépenses du budget
        elif form_type == "form_budget_expenses":
            description = request.form.get("description_budget_expenses")
            amount = request.form.get("amount_budget_expenses")
            if description and amount:
                try:
                    amount = float(amount)
                    session["budget_expenses"].append({"description": description, "amount": amount})
                    update_user_data(uid, {
                        "expenses": session["expenses"],
                        "revenus": session["revenus"],
                        "budget": session["budget"],
                        "budget_expenses": session["budget_expenses"]
                    })
                    if sum(float(exp["amount"]) for exp in session["budget_expenses"]) >= (session["budget"] * 0.8):
                        flash("Attention, vous avez dépensé plus de 80% de votre budget")
                    return redirect("/")
                except ValueError:
                    pass
        # Si le formulaire est celui de la réinitialisation du budget
        elif form_type == "reset_budget":
            flash("Budget réinitialisé avec succès")
            session["budget"] = 0
            session["budget_expenses"] = []
            update_user_data(uid, {
                "expenses": session["expenses"],
                "revenus": session["revenus"],
                "budget": session["budget"],
                "budget_expenses": session["budget_expenses"]
            })
            return redirect("/")

    # Calculs des résultats totaux après chaque mis à jour de la session
    total_depenses = sum(float(exp["amount"]) for exp in session["expenses"])
    total_revenus = sum(float(inc["amount"]) for inc in session["revenus"])
    total_budget_expenses = sum(float(exp["amount"]) for exp in session["budget_expenses"])
    remaining_budget = (session["budget"] or 0) - total_budget_expenses

    # Calcul du pourcentage de différence entre les revenus et les dépenses
    montant_difference = total_revenus - total_depenses
    if total_depenses > 0:
        percentage_result = (montant_difference * 100) / total_depenses
    else:
        percentage_result = 0

    percentage_result = round(percentage_result, 2)

    # Définition de la class HTML des animations en overlay
    div_class=""

    if percentage_result >= 75:
        flash("75% des revenus au-dessus des dépenses! JACKPOT!")
        div_class = "jackpot"

    if percentage_result <= -75:
        flash("75% des dépenses au-dessus des revenus! Attention!")
        div_class = "pauvrete"

    return render_template(
        "index.html",
        total_depenses=f"{total_depenses:.2f}", # Total des dépenses formaté en 2 décimales
        total_revenus=f"{total_revenus:.2f}", # Total des revenus formaté en 2 décimales
        expenses=session["expenses"], # Liste des dépenses
        revenus=session["revenus"], # Liste des revenus
        budget=session["budget"], # Budget actuel
        budget_expenses=session["budget_expenses"], # Liste des dépenses du budget
        remaining_budget=f"{remaining_budget:.2f}", # Budget restant formaté en 2 décimales
        montant_difference=f"{montant_difference:.2f}", # Montant de la différence formaté en 2 décimales
        percentage_result=percentage_result, # Pourcentage de la différence
        div_class=div_class # Class HTML pour les animations en overlay
    )

# Fonction permettant d'effacer l'entièreté des dépenses
@app.route("/effacer_depenses", methods=["POST"])
def effacer_depenses():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("auth_page"))
    flash("Dépenses effacées avec succès")
    session["expenses"] = []
    session.modified = True
    update_user_data(uid, {
                "expenses": session["expenses"],
                "revenus": session["revenus"],
                "budget": session["budget"],
                "budget_expenses": session["budget_expenses"]
            })
    return redirect("/")

# Fonction permettant d'effacer l'entièreté des revenus
@app.route("/effacer_revenus", methods=["POST"])
def effacer_revenus():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("auth_page"))
    flash("Revenus effacés avec succès")
    session["revenus"] = []
    session.modified = True
    update_user_data(uid, {
                "expenses": session["expenses"],
                "revenus": session["revenus"],
                "budget": session["budget"],
                "budget_expenses": session["budget_expenses"]
            })
    return redirect("/")

# Fonction permettant d'effacer une seule dépense
@app.route("/retirer_une_depense", methods=["POST"])
def retirer_une_depense():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("auth_page"))

    index = int(request.form.get("index"))
    session["expenses"].pop(index)
    update_user_data(uid, {
        "expenses": session["expenses"],
        "revenus": session["revenus"],
        "budget": session["budget"],
        "budget_expenses": session["budget_expenses"]
    })
    return redirect("/")

# Fonction permettant d'effacer un seul revenu
@app.route("/retirer_un_revenu", methods=["POST"])
def retirer_un_revenu():
    uid = session.get("uid")
    if not uid:
        return redirect(url_for("auth_page"))

    index = int(request.form.get("index"))
    session["revenus"].pop(index)
    update_user_data(uid, {
        "expenses": session["expenses"],
        "revenus": session["revenus"],
        "budget": session["budget"],
        "budget_expenses": session["budget_expenses"]
    })
    return redirect("/")

# Fonction gérant le système d'authentification
@app.route("/auth", methods=["GET", "POST"])
def auth_page():
    if request.method == "POST":
        email = request.form.get("email")
        password = request.form.get("password")
        action = request.form.get("action")

        if action == "login":
            user = login(email, password)
            if user:
                session["user"] = user["idToken"]
                session["uid"] = user["localId"]
                return redirect("/")

        elif action == "signup":
            user = signup(email, password)
            if user:
                session["user"] = user["idToken"]
                session["uid"] = user["localId"]
                return redirect("/")

    return render_template("auth.html")

# Fonction de déconnexion
@app.route("/logout")
def logout():
    session.pop("user", None)
    session.pop("uid", None)
    return redirect(url_for("auth_page"))

# Fonction gérant la génération du graphique
@app.route('/plot.png')
def plot_png():
    ys = [total_depenses, total_revenus] # Valeurs des dépenses et revenus sur l'axe des Y
    fig = create_figure(ys) # Création du graphique avec les données
    output = io.BytesIO() # Création d'un buffer pour stocker l'image
    FigureCanvas(fig).print_png(output) # Sauvegarde du graphique en format PNG dans le buffer
    return Response(output.getvalue(), mimetype='image/png') # Retour de l'image PNG comme réponse HTTP

def create_figure(ys):
    fig = Figure(facecolor='none') # Création d'un graphique avec un fond transparent
    axis = fig.add_subplot(1, 1, 1, facecolor='none') #Ajout d'un subplot avec un fond transparent
    xs = ["Dépenses", "Revenus"] # Valeurs des mots dépenses et revenus sur l'axe des X
    bars = axis.bar(xs, ys, color=['#ff5858', '#6cc13c']) # Création des barres du graphique avec spécification des couleurs

    axis.set_title('Total Dépenses vs Revenus', color='white') # Titre du graphique
    axis.set_ylabel('Montant ($)', color='white') # Label de l'axe des Y
    axis.set_ylim(0, max(ys) + 10) # Limite de l'axe des Y

    # Ajout des valeurs sur les barres
    for bar in bars:
        height = bar.get_height()
        axis.text(bar.get_x() + bar.get_width() / 2.0, height, f'{height}', ha='center', va='bottom', color='white')

    # Dissimulation des bordures
    axis.spines['top'].set_visible(False)
    axis.spines['right'].set_visible(False)
    axis.spines['left'].set_visible(False)
    axis.spines['bottom'].set_visible(False)

    # Dissimulation des graduations des axes
    axis.tick_params(left=False, bottom=False)

    # Retour du graphique
    return fig

if __name__ == "__main__":
    app.run(debug=True)