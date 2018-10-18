# --------------------------------
# Setting up imports and connect to server
# --------------------------------
import math
import time
import krpc
conn = krpc.connect(name='Launch into orbit')
vessel = conn.space_center.active_vessel

# ----------------------------------------------------------------------------
# Launch parameters
# from: https://forum.kerbalspaceprogram.com/index.php?/topic/130742-14x13x122-krpc-control-
# the-game-using-c-c-java-lua-python-ruby-haskell-c-arduino-v047-27th-july-2018/&page=11
# ----------------------------------------------------------------------------
MAX_AUTO_STAGE = 0  # last stage to separate automatically
REFRESH_FREQ = 5    # refresh rate
ALL_FUELS = ('LiquidFuel', 'SolidFuel')

# ----------------------------------------------------------------------------
# Main loop
# ----------------------------------------------------------------------------
def main():
    #  sc = conn.space_center
    v = vessel

    # continue checking until user quits program
    while True:
        # check autostage 'REFRESH_FREQ' times per second
        for t in range(REFRESH_FREQ):
            autostage(v)
            time.sleep(1.0 / REFRESH_FREQ)
        show_stage_stats(v) # Every second, print the fuel data per stage!
        break

# ----------------------------------------------------------------------------
# staging logic
# ----------------------------------------------------------------------------
def autostage(vessel):
    '''activate next stage when there is no fuel left in the current stage'''
    if out_of_stages(vessel):
        return
    res = get_resources(vessel)
    interstage = True   # flag to check if this is a fuel-less stage
    for fueltype in ALL_FUELS:
        if out_of_fuel(res, fueltype):
            next_stage(vessel)
            return
        if res.has_resource(fueltype):
            interstage = False
    if interstage:
        next_stage(vessel)

def show_stage_stats(vessel):
    '''for each available stage, bottom to top, show available fuel'''
    print('')
    # iterate from largest stage to final stage to be used
    for stage_num in stages_bottom_to_top(vessel):
        res = get_resources(vessel)
        for fueltype in ALL_FUELS:
            if res.max(fueltype) > 0:
                frac = res.amount(fueltype) / res.max(fueltype)
                print('Stage {}   - {} percentage: {:3.0%}'.format(
                   stage_num,
                   fueltype,
                   frac))

# ----------------------------------------------------------------------------
# Helper functions
# ----------------------------------------------------------------------------
def out_of_stages(vessel):
    '''True if no more stages left to activate'''
    return vessel.control.current_stage <= MAX_AUTO_STAGE

def get_resources(vessel):
    '''get resources of the vessel in the decouple stage'''
    return vessel.resources_in_decouple_stage(
       vessel.control.current_stage - 1,
       cumulative=False)

def out_of_fuel(resource, fueltype):
    '''return True if there is fuel capacity of the fueltype, but no fuel'''
    return resource.max(fueltype) > 0 and resource.amount(fueltype) == 0

def next_stage(vessel):
    '''activate the next stage'''
    vessel.control.activate_next_stage()

def stages_bottom_to_top(vessel):
    '''return an iterator that lists all available stage numbers, bottom to top'''
    return range(vessel.control.current_stage - 1, MAX_AUTO_STAGE - 1, -1)

# --------------------------------
# Set orbital parameters
# --------------------------------
turn_start_altitude = 250  # meters
turn_end_altitude = 45000  # meters
target_altitude = 100000  # meters

# --------------------------------
# Set up streams for telemetry
# --------------------------------
ut = conn.add_stream(getattr, conn.space_center, 'ut')
altitude = conn.add_stream(getattr, vessel.flight(), 'mean_altitude')
apoapsis = conn.add_stream(getattr, vessel.orbit, 'apoapsis_altitude')
srb_fuel = conn.add_stream(vessel.resources.amount, 'SolidFuel')
liq_fuel = conn.add_stream(vessel.resources.amount, 'LiquidFuel')
# parameters that are not working properly
# liq_fuel_3 = conn.add_stream(vessel.resources.amount, 'LiquidFuel')
# liq_fuel_2 = conn.add_stream(vessel.resources.amount, 'LiquidFuel')
# fuel_amount = conn.get_call(vessel.resources.amount, 'SolidFuel')
# periapsis = conn.add_stream(getattr, vessel.orbit, 'periapsis_altitude')
# stage_2_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
# stage_3_resources = vessel.resources_in_decouple_stage(stage=2, cumulative=False)
# srb_fuel = conn.add_stream(stage_2_resources.amount, 'SolidFuel')

# --------------------------------
# Set up UI Overlay
# --------------------------------
canvas = conn.ui.stock_canvas

# Get the size of the game window in pixels
screen_size = canvas.rect_transform.size

# Add a panel to contain the UI elements
panel = canvas.add_panel()

# Position the panel on the left of the screen
rect = panel.rect_transform
rect.size = (200, 150)
rect.position = (150-(screen_size[0]/2), 0)

# Add some text displaying the total engine thrust
text = panel.add_text("Thrust: 0 kN")
text.rect_transform.position = (0, -20)
text.color = (1, 1, 1)
text.size = 12

text2 = panel.add_text("Periapsis: 0 km")
text2.rect_transform.position = (0, -5)
text2.color = (1, 1, 1)
text2.size = 12

text3 = panel.add_text("Apoapsis: 0 km")
text3.rect_transform.position = (0, 10)
text3.color = (1, 1, 1)
text3.size = 12

# text4 = panel.add_text("All Fuels")
# text4.rect_transform.position = (0, 25)
# text4.color = (1, 1, 1)
# text4.size = 12

# text4.content = 'All Fuel:  ' % (vessel.resources.amount.liquidfuel)

# Add a button to Launch
button = panel.add_button("Launch!")
button.rect_transform.position = (0, 45)

# Set up a stream to monitor the Launch! button
button_clicked = conn.add_stream(getattr, button, 'clicked')

while True:
    # Handle the throttle button being clicked
    if button_clicked():
        break

# --------------------------------
# Pre-launch setup
# --------------------------------
vessel.control.sas = False
vessel.control.rcs = False
vessel.control.throttle = 1.0

# --------------------------------
# Launch!
# --------------------------------
# Countdown...
print('3...')
time.sleep(1)
print('2...')
time.sleep(1)
print('1...')
time.sleep(1)
print('Launch!')

# Activate the first stage
vessel.control.activate_next_stage()
vessel.auto_pilot.engage()
vessel.auto_pilot.target_pitch_and_heading(90, 90)

# Main ascent loop
# srbs_separated = False  # old code from tutorial for Solid sep only
turn_angle = 0
while True:

    text.content = 'Thrust: %d kN' % (vessel.thrust / 1000)
    text2.content = 'Apoapsis: %d km' % (vessel.orbit.apoapsis_altitude / 1000)
    text3.content = 'Periapsis: %d km' % (vessel.orbit.periapsis_altitude / 1000)

    print('vessel.periapsis')
    print('vessel.orbit.periapsis')
    # Gravity turn
    if altitude() > turn_start_altitude and altitude() < turn_end_altitude:
        frac = ((altitude() - turn_start_altitude) /
                (turn_end_altitude - turn_start_altitude))
        new_turn_angle = frac * 90
        if abs(new_turn_angle - turn_angle) > 0.5:
            turn_angle = new_turn_angle
            vessel.auto_pilot.target_pitch_and_heading(90-turn_angle, 90)

    # Separate SRBs when finished # old code from tutorial for Solid sep only
    # if not srbs_separated:
        # if srb_fuel() < 0.1:
            # vessel.control.activate_next_stage()
            # srbs_separated = True
            # print('SRBs separated')

    # running staging loop
    main()

    # Decrease throttle when approaching target apoapsis
    if apoapsis() > target_altitude*0.9:
        print('Approaching target apoapsis')
        break

# Disable engines when target apoapsis is reached
vessel.control.throttle = 0.25
while apoapsis() < target_altitude:
    text.content = 'Thrust: %d kN' % (vessel.thrust / 1000)
    text2.content = 'Apoapsis: %d km' % (vessel.orbit.apoapsis_altitude / 1000)
    text3.content = 'Periapsis: %d km' % (vessel.orbit.periapsis_altitude / 1000)
    pass
print('Target apoapsis reached')
vessel.control.throttle = 0.0

# Wait until out of atmosphere
print('Coasting out of atmosphere')
while altitude() < 70500:
    pass

def orbital_planning():
    # Plan circularization burn (using vis-viva equation)
    print('Planning circularization burn')
    mu = vessel.orbit.body.gravitational_parameter
    r = vessel.orbit.apoapsis
    a1 = vessel.orbit.semi_major_axis
    a2 = r
    v1 = math.sqrt(mu*((2./r)-(1./a1)))
    v2 = math.sqrt(mu*((2./r)-(1./a2)))
    delta_v = v2 - v1
    node = vessel.control.add_node(
        ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

    # Calculate burn time (using rocket equation)
    F = vessel.available_thrust
    Isp = vessel.specific_impulse * 9.82
    m0 = vessel.mass
    m1 = m0 / math.exp(delta_v/Isp)
    flow_rate = F / Isp
    burn_time = (m0 - m1) / flow_rate

# Plan circularization burn (using vis-viva equation)
print('Planning circularization burn')
mu = vessel.orbit.body.gravitational_parameter
r = vessel.orbit.apoapsis
a1 = vessel.orbit.semi_major_axis
a2 = r
v1 = math.sqrt(mu*((2./r)-(1./a1)))
v2 = math.sqrt(mu*((2./r)-(1./a2)))
delta_v = v2 - v1
node = vessel.control.add_node(
    ut() + vessel.orbit.time_to_apoapsis, prograde=delta_v)

# Calculate burn time (using rocket equation)
F = vessel.available_thrust
Isp = vessel.specific_impulse * 9.82
m0 = vessel.mass
m1 = m0 / math.exp(delta_v/Isp)
flow_rate = F / Isp
burn_time = (m0 - m1) / flow_rate

# Orientate ship
print('Orientating ship for circularization burn')
vessel.auto_pilot.reference_frame = node.reference_frame
vessel.auto_pilot.target_direction = (0, 1, 0)
# calculate burn time
burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
# set up a statement to break the wait period if reorienting is taking too long
if ut() < burn_ut:
    vessel.auto_pilot.wait()
else:
    pass

# Wait until burn
print('Waiting until circularization burn')
# burn_ut = ut() + vessel.orbit.time_to_apoapsis - (burn_time/2.)
lead_time = 10
conn.space_center.warp_to(burn_ut - lead_time)
print('Ready to execute burn')

time_to_apoapsis = conn.add_stream(getattr, vessel.orbit, 'time_to_apoapsis')
while time_to_apoapsis() - (burn_time/2.) > 0:
    pass
# print('Executing burn')

# Orbit Burn Loop
while True:
    # Execute burn
    print('Executing burn')
    vessel.control.throttle = 1.0
    text.content = 'Thrust: %d kN' % (vessel.thrust / 1000)
    text2.content = 'Apoapsis: %d km' % (vessel.orbit.apoapsis_altitude / 1000)
    text3.content = 'Periapsis: %d km' % (vessel.orbit.periapsis_altitude / 1000)
    # running staging loop
    main()
    # time.sleep(burn_time - 0.1)
    if vessel.orbit.periapsis_altitude > 0.93*target_altitude:
        print('Fine tuning')
        vessel.control.throttle = 0.05
    # remaining_burn = conn.add_stream(node.remaining_burn_vector, node.reference_frame)
    # while remaining_burn()[1] > 0:
    #     pass
    if vessel.orbit.periapsis_altitude > 0.999 * target_altitude:
        vessel.control.throttle = 0.0
        node.remove()
        print('Launch complete')
        break


