from manim import *
import random
import numpy as np

class GaltonBoardBuoyancy(Scene):
    
    settings = {
        "animation_duration": 16,
        "particle_count": 200,
        "particle_delay": 1,
        "pin_size": .2,
        "vertical_gap": .6,
        "horizontal_gap": .4,
        "pin_rows": 7,
        "start_x": -3,
        "start_y": -3,
        "movement_duration": 2,
        "particle_size": .05,
        "particle_start": [-3, -4.3, 0],
        # Physics parameters
        "fluid_density": 1000,  # kg/m³ (water)
        "particle_density": 900,  # kg/m³ (less than water to float)
        "particle_volume": 0.001,  # m³
        "gravity": 9.81,  # m/s²
        "fluid_viscosity": 0.001,  # Pa·s (water)
        "time_step": 0.016  # seconds (typical for 60fps)
    }
    
    current_frame = 0

    def calculate_buoyancy_acceleration(self):
        """Calculate acceleration due to buoyancy"""
        particle_mass = self.settings["particle_density"] * self.settings["particle_volume"]
        fluid_displacement = self.settings["fluid_density"] * self.settings["particle_volume"]
        
        buoyant_force = fluid_displacement * self.settings["gravity"]
        weight = particle_mass * self.settings["gravity"]
        net_force = buoyant_force - weight
        
        acceleration = net_force / particle_mass
        return acceleration

    def calculate_terminal_velocity(self):
        """Calculate terminal velocity considering drag force"""
        particle_mass = self.settings["particle_density"] * self.settings["particle_volume"]
        net_force = self.calculate_buoyancy_acceleration() * particle_mass
        
        radius = (self.settings["particle_volume"] * 3 / (4 * np.pi)) ** (1/3)
        drag_coefficient = 6 * np.pi * self.settings["fluid_viscosity"] * radius
        
        terminal_velocity = net_force / drag_coefficient
        return terminal_velocity

    def apply_buoyancy_effect(self, progress):
        """Modify the progress value to simulate buoyancy effect"""
        acceleration = self.calculate_buoyancy_acceleration()
        time = progress * self.settings["movement_duration"]
        velocity = acceleration * time
        
        terminal_velocity = self.calculate_terminal_velocity()
        velocity = min(velocity, terminal_velocity)
        
        modified_progress = progress + (velocity * self.settings["time_step"]) / 10
        return np.clip(modified_progress, 0, 1)

    def create_container(self):
        container = Rectangle(
            width=6.5,
            height=8.0,
            stroke_color=BLUE,
            stroke_width=2,
            fill_color=BLUE,
            fill_opacity=0.15
        )
        container.move_to([-3, -0.5, 0])
        return container

    def construct(self):
        container = self.create_container()
        self.play(Create(container), run_time=1)
        
        results = self.create_results_display()
        particle_counter = self.create_counter_display()
        pins = self.create_pin_grid()
        collision_points = self.create_collision_points()
        particles = self.create_particles(collision_points)

        pins.set_stroke(color=BLUE_C, width=1.5)

        def update_simulation(results):
            time_per_move = GaltonBoardBuoyancy.settings["movement_duration"]
            frames_per_move = time_per_move * self.camera.frame_rate
            self.current_frame += 1

            for particle in particles:
                if particle.active and self.current_frame > particle.start_time:
                    base_progress = (self.current_frame - particle.start_time) / frames_per_move
                    if base_progress <= 1.0:
                        modified_progress = self.apply_buoyancy_effect(base_progress)
                        position = particle.trajectory.point_from_proportion(
                            rate_functions.ease_out_cubic(modified_progress)
                        )
                        particle.shape.move_to(position)
                    else:
                        update_particle_count()
                        update_bin_count(particle.bin_index)
                        particle.active = False

        def update_particle_count():
            current = particle_counter[0].get_value()
            particle_counter[0].set_value(current + 1)

        def update_bin_count(bin_index):
            bin_cell = results.get_entries((1, bin_index + 1))
            current = bin_cell.get_value()
            bin_cell.set_value(current + 1)

        self.play(FadeIn(pins, run_time=1))
        self.play(FadeIn(results, run_time=1))
        self.play(FadeIn(particle_counter, run_time=1))

        elements = VGroup(results, particle_counter)
        for particle in particles:
            elements.add(particle.shape)

        duration = GaltonBoardBuoyancy.settings["animation_duration"]
        self.play(UpdateFromFunc(elements, update_simulation), run_time=duration)
        self.wait(3)

    def create_results_display(self):
        results = IntegerTable(
            [[0, 0, 0, 0, 0, 0, 0, 0],],
            line_config={"stroke_width": 1, "color": YELLOW},
            include_outer_lines=False
        )
        results.scale(.5)
        results.shift(UP * 3.7).shift(LEFT * 3)
        return results
    
    def create_counter_display(self):
        count = Integer(0).shift(RIGHT * 4).shift(DOWN * .6)
        label = Text('Items count:', font_size=28)
        label.next_to(count, LEFT)
        return VGroup(count, label)   
    
    def create_pin_grid(self):
        pins = VGroup()
        for row in range(self.settings["pin_rows"]):
            y_pos = (self.settings["start_y"] + row * self.settings["vertical_gap"])
            x_start = (self.settings["start_x"] - row * self.settings["horizontal_gap"])
            for col in range(row + 1):
                x_pos = x_start + (col * self.settings["horizontal_gap"]) * 2
                pin = RegularPolygon(n=6, radius=self.settings["pin_size"], start_angle=.5)
                pin.shift(UP * y_pos + RIGHT * x_pos)
                pins.add(pin)
        return pins
    
    def create_collision_points(self):
        points = [[None for _ in range(self.settings["pin_rows"] + 1)] 
                 for _ in range(self.settings["pin_rows"] + 1)]

        for row in range(self.settings["pin_rows"] + 1):
            y_pos = (self.settings["start_y"] + row * self.settings["vertical_gap"])
            x_start = (self.settings["start_x"] - row * self.settings["horizontal_gap"])
            for col in range(row + 1):
                x_pos = x_start + (col * self.settings["horizontal_gap"]) * 2
                points[row][col] = [x_pos, y_pos - self.settings["pin_size"] - .1, 0]

        return points
    
    def create_particles(self, collision_points):
        particles = []
        start_frame = 0
        bin_counts = [0] * 8

        for _ in range(self.settings["particle_count"]):
            particle = Particle()
            
            shape = Circle(
                radius=self.settings["particle_size"],
                stroke_color=GREEN_A,
                stroke_width=1,
                fill_color=GREEN_A,
                fill_opacity=0.8
            )
            
            path_number = self.generate_path_number()
            bin_index = bin(path_number).count('1')
            bin_counts[bin_index] += 1

            trajectory = self.calculate_trajectory(collision_points, path_number, bin_counts[bin_index])

            particle.trajectory = trajectory
            particle.shape = shape
            particle.bin_index = bin_index
            particle.start_time = start_frame
            
            start_frame += self.settings["particle_delay"]

            self.add(shape)
            shape.move_to(self.settings["particle_start"])

            particles.append(particle)

        return particles

    def generate_path_number(self):
        return random.randrange(128)
    
    def calculate_trajectory(self, collision_points, path_number, stack_position):
        row_capacity = 3
        stack_row = (stack_position - 1) // row_capacity
        stack_col = (stack_position - 1) % row_capacity 
        
        trajectory = Line(
            self.settings["particle_start"], 
            collision_points[0][0], 
            stroke_width=1
        )
        
        current_point = collision_points[0][0]
        binary_path = bin(path_number)[2:].zfill(7)
        row = 1
        col = 0
        
        for direction in binary_path:
            if direction == '0':
                path_segment = ArcBetweenPoints(
                    current_point, 
                    collision_points[row][col], 
                    angle=-PI/2, 
                    stroke_width=1
                )
                current_point = collision_points[row][col]
            else:
                col += 1
                path_segment = ArcBetweenPoints(
                    current_point, 
                    collision_points[row][col], 
                    angle=PI/2, 
                    stroke_width=1
                )
                current_point = collision_points[row][col]
            trajectory.append_vectorized_mobject(path_segment)
            row += 1

        dot_width = .1
        dot_height = .1
        final_x = current_point[0]
        
        if stack_col == 0:
            final_x -= dot_width
        elif stack_col == 2:
            final_x += dot_width

        final_y = current_point[1] + 2.4 - dot_height * stack_row
        final_segment = Line(current_point, [final_x, final_y, 0], stroke_width=1)
        trajectory.append_vectorized_mobject(final_segment)

        return trajectory

class Particle:
    def __init__(self):
        self.shape = None
        self.trajectory = None
        self.start_time = 0
        self.bin_index = 0
        self.active = True