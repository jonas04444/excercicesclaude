from ortools.sat.python import cp_model

print("🔧 Test OR-Tools minimal...")

# Créer un modèle simple
model = cp_model.CpModel()

# Variable booléenne
x = model.NewBoolVar('x')

# Contrainte simple
model.Add(x == 1)

# Résolution
solver = cp_model.CpSolver()
print("🚀 Lancement résolution...")

status = solver.Solve(model)

if status == cp_model.OPTIMAL:
    print(f"✅ OR-Tools fonctionne ! x = {solver.Value(x)}")
else:
    print(f"❌ Problème: status = {status}")