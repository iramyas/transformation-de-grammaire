import glob
from itertools import combinations

class Grammaire:
    def __init__(self):
        self.regles = {}
        self.axiome = None  
        self.compteur = 1    #pour generer les non terminaux

    def ajouter_regle(self, gauche, droites):
        if gauche not in self.regles:
            self.regles[gauche] = []
        self.regles[gauche].extend(droites)
        if self.axiome is None:
            self.axiome = gauche  # Définir l'axiome lors de l'ajout de la première règle

    def generer_nom(self, prefixe):
        i = 1
        while f"{prefixe}{i}" in self.regles:
            i += 1
        return f"{prefixe}{i}"

def lire_grammaire(fichier):
    """Lit une grammaire depuis un fichier et traite E comme epsilon."""
    grammaire = Grammaire()
    with open(fichier, 'r') as f:
        for ligne in f:
            ligne = ligne.strip()
            if not ligne or ligne.startswith('#'):
                continue
            gauche, droite = ligne.split(':')
            gauche = gauche.strip()
            productions = []
            for partie in droite.split('|'):
                partie = partie.strip()
                if 'E' in partie:  # Traite les epsilon-productions comme une liste vide []
                    productions.append([])  
                else:
                    if partie:
                        productions.append(partie.split())
            grammaire.ajouter_regle(gauche, productions)
    return grammaire

def eliminer_epsilon_rules(grammaire):
    """Élimine les epsilon-productions."""
    nullable = set()

    # Détecter les non-terminaux annulables
    changed = True
    while changed:
        changed = False
        for non_term, prods in grammaire.regles.items():
            if non_term not in nullable:
                for prod in prods:
                    if not prod or all(symbol in nullable for symbol in prod):
                        nullable.add(non_term)
                        changed = True
                        break

    # Réécrire les productions sans epsilon-productions
    resultat = Grammaire()
    for non_term, prods in grammaire.regles.items():
        new_prods = set()
        for prod in prods:
            if not prod:
                continue  # Ignorer les epsilon-productions
            for i in range(len(prod) + 1):
                for nullable_positions in combinations(range(len(prod)), i):
                    new_prod = [s for j, s in enumerate(prod) if j not in nullable_positions]
                    new_prods.add(tuple(new_prod))
        if new_prods:
            resultat.ajouter_regle(non_term, [list(p) for p in new_prods])

    # Si le non-terminal est nullable, ajouter une règle vide
    for non_term in resultat.regles:
        if non_term in nullable:
            resultat.ajouter_regle(non_term, [[]])

    return resultat

def chomsky(grammaire):
    """Transforme une grammaire en forme normale de Chomsky (CNF)."""
    resultat = Grammaire()
    grammaire = eliminer_epsilon_rules(grammaire)

    # Étape 1 : Remplacer les terminaux dans les productions de longueur > 1
    for non_term, prods in grammaire.regles.items():
        for prod in prods:
            new_prod = []
            for symbol in prod:
                if symbol.islower():  # Si c'est un terminal
                    # Créer un nouveau non-terminal pour ce terminal
                    new_non_term = next(
                        (nt for nt, rules in resultat.regles.items()
                         if len(rules) == 1 and rules[0] == [symbol]),
                        None
                    )
                    if not new_non_term:  # Si le terminal n'a pas encore de règle
                        new_non_term = resultat.generer_nom("X")
                        resultat.ajouter_regle(new_non_term, [[symbol]])
                    new_prod.append(new_non_term)
                else:
                    new_prod.append(symbol)

            # Décomposer si la production a plus de 2 symboles
            while len(new_prod) > 2:
                new_non_term = resultat.generer_nom("Y")
                resultat.ajouter_regle(new_non_term, [new_prod[-2:]])
                new_prod = new_prod[:-2] + [new_non_term]

            # Ajouter la production finale
            if len(new_prod) == 2:
                resultat.ajouter_regle(non_term, [new_prod])

    # Éliminer les productions invalides et récursives
    for non_term in list(resultat.regles.keys()):
        # Supprimer les productions de la forme A -> A
        resultat.regles[non_term] = [prod for prod in resultat.regles[non_term] if prod != [non_term]]

        # Supprimer les productions avec un seul non-terminal
        resultat.regles[non_term] = [prod for prod in resultat.regles[non_term] if len(prod) > 0]

        # Éliminer les récursions directes
        if non_term in resultat.regles:
            for prod in resultat.regles[non_term]:
                if prod[0] == non_term:
                    # Si la production commence par le même non-terminal, on l'élimine
                    resultat.regles[non_term].remove(prod)

    return resultat


def greibach(grammaire):
    """Transforme une grammaire en forme normale de Greibach (GNF)."""
    resultat = Grammaire()

    # Conversion préliminaire en CNF
    cnf = chomsky(grammaire)

    # Étape 1 : Remplacer les productions qui commencent par des non-terminaux
    for A in cnf.regles:
        for prod in cnf.regles[A]:
            if not prod:
                continue  # Ignore les productions vides (epsilon)

            # Si la production commence par un terminal, on l'ajoute directement
            if prod[0].islower():
                resultat.ajouter_regle(A, [list(prod)])
            else:
                # Si la production commence par un non-terminal, on remplace par ses productions
                first_nt = prod[0]
                for sub_prod in cnf.regles.get(first_nt, []):
                    if sub_prod and sub_prod[0].islower():
                        # Créer une nouvelle production qui commence par le terminal
                        new_prod = [sub_prod[0]] + prod[1:]  # Terminal + reste de la production
                        resultat.ajouter_regle(A, [new_prod])

    return resultat


def ecrire_grammaire(grammaire, fichier):
    """Écrit la grammaire dans un fichier."""
    with open(fichier, 'w') as f:
        for gauche, droites in grammaire.regles.items():
            productions = []
            for prod in droites:
                if not prod:  # Production vide (epsilon)
                    productions.append('E')
                else:
                    productions.append(' '.join(prod))
            f.write(f"{gauche} : {' | '.join(productions)}\n")

def traiter_fichiers():
    """Traite tous les fichiers .general dans le répertoire examples."""
    fichiers = glob.glob("examples/*.general")
    for fichier in fichiers:
        grammaire = lire_grammaire(fichier)

        chomsky_file = fichier.replace('.general', '.chomsky')
        greibach_file = fichier.replace('.general', '.greibach')

        # Traitement de la grammaire en Chomsky
        grammaire_chomsky = chomsky(grammaire)
        ecrire_grammaire(grammaire_chomsky, chomsky_file)

        # Traitement de la grammaire en Greibach
        grammaire_greibach = greibach(grammaire)
        ecrire_grammaire(grammaire_greibach, greibach_file)

if __name__ == "__main__":
    traiter_fichiers()
