from ortools.sat.python import cp_model

model = cp_model.CpModel()

# 2. Créer des variables (3 services, chacun peut prendre 0 à 5 voyages)
services = {}
for i in range(3):
    services[i] = model.NewIntVar(0, 5, f"service_{i}")

# 3. Contrainte : le total des voyages doit être exactement 10
model.Add(sum(services.values()) == 10)
model.Add(services[0] > services[1])
for i in range(3):
    model.Add(services[i] >= 2)

# 4. Résoudre
solver = cp_model.CpSolver()
status = solver.Solve(model)

# 5. Afficher
if status == cp_model.OPTIMAL:
    for i in range(3):
        print(f"Service {i} : {solver.Value(services[i])} voyages")