#!/usr/bin/env python
from pydy import *
from sympy import factor

# Create a Newtonian reference frame
N = NewtonianReferenceFrame('N')

# Declare parameters, coordinates, speeds
params = N.declare_parameters('l1 l2 l3 ma mb g I11 I22 I33 I12 I23 I13 I J K T')
q, qd = N.declare_coords('q', 7)
u, ud = N.declare_speeds('u', 7)
# Unpack the lists
l1, l2, l3, ma, mb, g, I11, I22, I33, I12, I23, I13, I, J, K, T = params
q1, q2, q3, q4, q5, q6, q7 = q
q1d, q2d, q3d, q4d, q5d, q6d, q7d = qd
u1, u2, u3, u4, u5, u6, u7 = u
u1d, u2d, u3d, u4d, u5d, u6d, u7d = ud

# Frame fixed to the rigid body
A = N.rotate("A", 'BODY312', (q1, q2, q3), I=(I11, I22, I33, 0, 0, I13))
B = A.rotate("B", 2, q4, I=(I, J, I, 0, 0, 0), I_frame=A)

# Create the point AO
AO = Point('AO')
# Locate AO relative to BO
BO = AO.locate('BO', l1*A[1] + l3*A[3])
# Position from AO to ABO
P_AO_ABO = mass_center(AO, [(AO, ma), (BO, mb)])
# Position from BO to ABO
P_BO_ABO = mass_center(BO, [(AO, ma), (BO, mb)])

# Locate the mass center of the system
ABO = N.O.locate('ABO', q5*N[1] + q6*N[2] + q7*N[3])
AO = ABO.locate('AO', -P_AO_ABO, mass=ma)
BO = ABO.locate('AO', -P_BO_ABO, mass=mb)

# Define the generalized speeds
u_rhs = [dot(A.ang_vel(), A[i]) for i in (1, 2, 3)] + \
        [dot(B.ang_vel(), A[2])] + \
        [dot(ABO.vel(), A[i]) for i in (1, 2, 3)]

# Form the list of equations mapping qdots to generalized speeds
qd_to_u_eqs = [Eq(ui, ui_rhs) for ui, ui_rhs in zip(u, u_rhs)]
# Form the matrix that maps qdot's to u's
qd_to_u = coefficient_matrix(u_rhs, qd)
adj = qd_to_u.adjugate().expand().subs(N.csqrd_dict).expand()
det = qd_to_u.det(method="berkowitz").expand().subs(N.csqrd_dict).expand()
u_to_qd = (adj / det).expand().subs({sin(q2)**2:1-cos(q2)**2}).expand()

qd_rhs = u_to_qd * Matrix(u)
# Create a list of kinematic differential equations
u_to_qd_eqs = []
for qdot, eqn in zip(qd, qd_rhs):
    u_to_qd_eqs.append(Eq(qdot, eqn.subs({sin(q2)/cos(q2): tan(q2)})))
    print u_to_qd_eqs[-1]

# Set velocities and angular velocities using only generalized speeds
A.abs_ang_vel = Vector(u1*A[1] + u2*A[2] + u3*A[3])
B.abs_ang_vel = Vector(u1*A[1] + u4*A[2] + u3*A[3])
ABO.abs_vel = Vector(u5*A[1] + u6*A[2] + u7*A[3])
AO.abs_vel = ABO.abs_vel + cross(A.ang_vel(N), -P_AO_ABO)
BO.abs_vel = ABO.abs_vel + cross(A.ang_vel(N), -P_BO_ABO)

print 'w_a =',A.abs_ang_vel
print 'w_b =',B.abs_ang_vel
print 'v_ao =',AO.abs_vel
print 'v_bo =',BO.abs_vel

mab = Symbol('mab')
m_subs_dict = {ma+mb:mab}
# Set accelerations and angular accelerations
A.abs_ang_acc = dt(A.abs_ang_vel, N).subs(m_subs_dict)
B.abs_ang_acc = dt(B.abs_ang_vel, N).subs(m_subs_dict)
AO.abs_acc = dt(AO.abs_vel, N).subs(m_subs_dict)
BO.abs_acc = dt(BO.abs_vel, N).subs(m_subs_dict)
print 'alpha_a =', A.abs_ang_acc
print 'alpha_b =', B.abs_ang_acc
print 'a_ao =', AO.abs_acc
print 'a_bo =', BO.abs_acc

# Apply gravity
N.gravity(g*N[3])
# Apply a torque between the two bodies
B.apply_torque(T*A[2], A)

# Form Kane's equations and solve them for the udots
kanes_eqns = N.form_kanes_equations()
for i in range(7):
    print kanes_eqns[i].lhs, '=', kanes_eqns[i].rhs.subs(m_subs_dict)
#dyndiffs, dd_subs = N.solve_kanes_equations(dummy_vars=True)