from cnf import *
from ortools.sat.python import cp_model

objects = ['Outlet', 'Rasp-Pi', 'Power-Board',
           'Arduino', 'Sensor-Board0', 'Sensor-Board1']
actuators = ['Fans', 'LEDs', 'Pump']
sensors = ['H-T0', 'Light0', 'Moisture0', 'H-T1', 'Light1', 'Moisture1',
           'Wlevel']
relations = ['working', 'connected', 'powered', 'signal', 'expected-result']

def powered(comp): return f'powered({comp})'
def working(comp): return f'working({comp})'
def connected(from_comp, to_comp):
    return f'connected({from_comp}, {to_comp})'
def signal(signal, component): return f'signal({signal}, {component})'
def rasp_pi_signal(the_signal): return signal(the_signal, 'Rasp-Pi')
def expected_result(actuator): return f'expected-result({actuator})'

def create_relation(name, model, variables):
    variables[name] = model.NewBoolVar(name)

def create_relations(relations, model, variables):
    for relation in relations: create_relation(relation, model, variables)

def create_working_relations(model, variables):
    create_relations([working(comp) for comp in objects + actuators + sensors],
                     model, variables)

def create_connected_relations(model, variables):
    # BEGIN STUDENT CODE
    connections = [
        ("Wlevel", "Arduino"),
        ("Sensor-Board1", "Arduino"),
        ("Sensor-Board0", "Arduino"),
        ("Arduino", "Power-Board"),
        ("Power-Board", "LEDs"),
        ("Power-Board", "Pump"),
        ("Power-Board", "Fans"),
        ("Arduino", "Rasp-Pi"),
        ("Rasp-Pi", "Arduino"),
        ("Outlet", "Rasp-Pi"),
        ("Outlet", "Power-Board"),

        ("H-T0", "Sensor-Board0"),
        ("Light0", "Sensor-Board0"),
        ("Moisture0", "Sensor-Board0"),

        ("H-T1", "Sensor-Board1"),
        ("Light1", "Sensor-Board1"),
        ("Moisture1", "Sensor-Board1")
    ]
    create_relations([connected(from_comp, to_comp) for (from_comp, to_comp) in connections],
                     model, variables)
    # END STUDENT CODE

def create_powered_relations(model, variables):
    # BEGIN STUDENT CODE
    create_relations([powered(comp) for comp in actuators + objects[0:3]],
                     model, variables)
    # END STUDENT CODE

def create_signal_relations(model, variables):
    # BEGIN STUDENT CODE
    sign_comps = []
    comps1 = ["Sensor-Board0", "Arduino", "Rasp-Pi"]
    signs1 = ["H-T0", "Light0", "Moisture0"]

    for sign in signs1:
        sign_comps.append((sign, sign))
        for comp in comps1:
            sign_comps.append((sign, comp))

    comps2 = ["Sensor-Board1", "Arduino", "Rasp-Pi"]
    signs2 = ["H-T1", "Light1", "Moisture1"]

    for sign in signs2:
        sign_comps.append((sign, sign))
        for comp in comps2:
            sign_comps.append((sign, comp))

    sign_comps.append(("Wlevel", "Wlevel"))
    sign_comps.append(("Wlevel", "Arduino"))
    sign_comps.append(("Wlevel", "Rasp-Pi"))

    for actuator in actuators:
        for obj in objects[1:4]:
            sign_comps.append((actuator, obj))

    create_relations([signal(sign, comp) for (sign, comp) in sign_comps],
                     model, variables)
    # END STUDENT CODE

def create_expected_result_relations(model, variables):
    # BEGIN STUDENT CODE
    create_relations([expected_result(actuator) for actuator in actuators], model,
                     variables)
    # END STUDENT CODE
    pass

def create_relation_variables(model):
    variables = {}
    create_working_relations(model, variables)
    create_connected_relations(model, variables)
    create_powered_relations(model, variables)
    create_signal_relations(model, variables)
    create_expected_result_relations(model, variables)
    return variables

def add_constraint_to_model(constraint, model, variables):
    for disj in (eval(constraint) if isinstance(constraint, str) else constraint):
        conv_disj = [variables[lit] if not is_negated(lit) else
                     variables[lit[1]].Not() for lit in disj]
        model.AddBoolOr(conv_disj)

def create_powered_constraint(from_comp, to_comp, model, variables):
    constraint = f"IFF('{powered(to_comp)}', AND('{connected(from_comp, to_comp)}',\
                                                 '{working(from_comp)}'))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_actuator_constraint(actuator, model, variables):
    constraint = f"IFF('{powered(actuator)}',\
                       AND('{connected('Power-Board', actuator)}',\
                           AND('{powered('Power-Board')}',\
                               AND('{working('Power-Board')}', '{signal(actuator, 'Power-Board')}'))))"
    add_constraint_to_model(constraint, model, variables)

def create_powered_constraints(model, variables):
    add_constraint_to_model(LIT(powered('Outlet')), model, variables)
    create_powered_constraint('Outlet', 'Rasp-Pi', model, variables)
    create_powered_constraint('Outlet', 'Power-Board', model, variables)
    for actuator in actuators:
        create_powered_actuator_constraint(actuator, model, variables)

def _create_signal_constraint(sig_from0, sig_to0, con_from, con_to, work, sig_from1, sig_from2, model, variables):
    constraint = f"IFF('{signal(sig_from0, sig_to0)}',\
                      AND('{connected(con_from, con_to)}',\
                        AND('{working(work)}', '{signal(sig_from1, sig_from2)}')\
                      )\
                   )"
    
    add_constraint_to_model(constraint, model, variables)

def create_signal_constraint(sig_from, comp_to, con_from, model, variables):
    _create_signal_constraint(sig_from, comp_to, con_from, comp_to, con_from, sig_from, con_from, model, variables)

def create_signal_constraints(model, variables):
    # BEGIN STUDENT CODE
    sig_constraints = []
    for i in range(2):
        HT_i = f"H-T{i}"
        L_i = f"Light{i}"
        M_i = f"Moisture{i}"
        SB_i = f"Sensor-Board{i}"
        sig_constraints.extend([
            (HT_i, SB_i, HT_i),
            (HT_i, "Arduino", SB_i),
            (HT_i, "Rasp-Pi", "Arduino"),
            (L_i, SB_i, L_i),
            (L_i, "Arduino", SB_i),
            (L_i, "Rasp-Pi", "Arduino"),
            (M_i, SB_i, M_i),
            (M_i, "Arduino", SB_i),
            (M_i, "Rasp-Pi", "Arduino")
        ])

    sig_constraints.extend([
        ("Wlevel", "Arduino", "Wlevel"),
        ("Wlevel", "Rasp-Pi", "Arduino"),
        ("LEDs", "Arduino", "Rasp-Pi"),
        ("LEDs", "Power-Board", "Arduino"),
        ("Fans", "Power-Board", "Arduino"),
        ("Fans", "Arduino", "Rasp-Pi"),
        ("Pump", "Arduino", "Rasp-Pi"),
        ("Pump", "Power-Board", "Arduino")
    ])

    for sig_constraint in sig_constraints:
        create_signal_constraint(*sig_constraint, model, variables)
    # END STUDENT CODE
    pass

def create_sensor_generation_constraint(sensor, model, variables):
    constraint = f"IFF('{signal(sensor, sensor)}','{working(sensor)}')"
    add_constraint_to_model(constraint, model, variables)

def create_sensor_generation_constraints(model, variables):
    # BEGIN STUDENT CODE
    sens_gen_constraints = [
        "Light0",
        "Moisture0",
        "H-T0",
        "Light1",
        "Moisture1",
        "H-T1",
        "Wlevel"
    ]
    
    for sens in sens_gen_constraints:
        create_sensor_generation_constraint(sens, model, variables)
    # END STUDENT CODE
    pass

def create_expected_result_constraint(actuator, sig1, sig2, sig3, model, variables):
    if sig3:
        constraint = f"IFF('{expected_result(actuator)}',\
                        AND('{working(actuator)}',\
                            AND('{powered(actuator)}',\
                                OR('{signal(sig1, 'Rasp-Pi')}', \
                                    OR('{signal(sig2, 'Rasp-Pi')}', '{signal(sig3, 'Rasp-Pi')}')\
                                )\
                            )\
                        )\
                    )"
    else:
        constraint = f"IFF('{expected_result(actuator)}',\
                        AND('{working(actuator)}',\
                            AND('{powered(actuator)}',\
                                OR('{signal(sig1, 'Rasp-Pi')}', '{signal(sig2, 'Rasp-Pi')}')\
                            )\
                        )\
                    )"
    
    add_constraint_to_model(constraint, model, variables)
    

def create_expected_result_constraints(model, variables):
    # BEGIN STUDENT CODE
    exp_res_constraints = [
        ("Fans", "H-T0", "H-T1", None),
        ("LEDs", "Light0", "Light1", None),
        ("Pump", "Moisture0", "Moisture1", "Wlevel")
    ]
    for exp_res_constraint in exp_res_constraints:
        create_expected_result_constraint(*exp_res_constraint, model, variables)
    # END STUDENT CODE
    pass

def create_constraints(model, variables):
    create_powered_constraints(model, variables)
    create_signal_constraints(model, variables)
    create_sensor_generation_constraints(model, variables)
    create_expected_result_constraints(model, variables)

def create_greenhouse_model():
    model = cp_model.CpModel()
    variables = create_relation_variables(model)
    create_constraints(model, variables)
    return (model, variables)
    
def collect_diagnosis(solver, variables):
    return set([var for var in variables
                if ((var.startswith('connected') or var.startswith('working')) and
                    solver.BooleanValue(variables[var]) == False)])

class DiagnosesCollector(cp_model.CpSolverSolutionCallback):
    def __init__(self, variables):
        cp_model.CpSolverSolutionCallback.__init__(self)
        # BEGIN STUDENT CODE
        self.variables = variables
        self.diagnoses = []
        # END STUDENT CODE

    def OnSolutionCallback(self):
        # Extract the connected and working relations that are False
        # BEGIN STUDENT CODE
        diag = set()
        for name, var in self.variables.items():
            if (name.startswith('connected') or name.startswith('working')) and self.Value(var) == 0:
                diag.add(name)
        self.diagnoses.append(diag)
        # END STUDENT CODE
        pass

def diagnose(observations):
    model, variables = create_greenhouse_model()
    add_constraint_to_model(observations, model, variables)

    collector = DiagnosesCollector(variables)
    diagnoses = []
    solver = cp_model.CpSolver()
    solver.SearchForAllSolutions(model, collector)
    # Remove all redundant diagnoses (those that are supersets
    #   of other diagnoses).
    # BEGIN STUDENT CODE
    unique_diagnoses = [set(d) for d in collector.diagnoses]
    minimal = []
    for s in unique_diagnoses:
        flag = False
        for t in unique_diagnoses:
            if t < s:
                flag = True
        if not flag:
            minimal.append(s)
    diagnoses = minimal
    # END STUDENT CODE

    return diagnoses
