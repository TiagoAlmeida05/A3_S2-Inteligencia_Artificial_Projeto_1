import pygame
import sys
import math

class Visualizer:
    def __init__ (self, width = 1200, height = 820, rows = 10, cols = 10 ):
        pygame.init()

        self.width = width
        self.height = height
        self.rows = rows
        self.cols = cols
        self.panel_width = 360
        self.screen = pygame.display.set_mode((self.width, self.height))
        pygame.display.set_caption("Self-Driving Rides Visualizer")
        self.clock = pygame.time.Clock()
        self.font = pygame.font.SysFont("dejavusansmono", 18)
        self.small_font = pygame.font.SysFont("dejavusansmono", 14)
        self.title_font = pygame.font.SysFont("dejavusansmono", 24, bold=True)

        self.paused = True
        self.speed_fps = 8
        self.last_auto_step_ms = 0

        self.selected_car_id = None
        self.selected_ride_id = None

        self.palette = {
            "car": (70, 145, 255),
            "car_active": (73, 214, 112),
            "waiting": (255, 196, 79),
            "destination": (88, 232, 143),
            "assigned": (255, 224, 122),
            "expired": (255, 90, 90),
            "text_dark": (9, 16, 24),
        }

    def _map_rect(self):
        return pygame.Rect(12, 12, self.width - self.panel_width - 24, self.height - 24)

    def _panel_rect(self):
        return pygame.Rect(self.width - self.panel_width, 0, self.panel_width, self.height)

    def _cell_geometry(self, state):
        self.rows = max(1, state.get("rows", self.rows))
        self.cols = max(1, state.get("cols", self.cols))
        map_rect = self._map_rect()
        cell_w = map_rect.width / self.cols
        cell_h = map_rect.height / self.rows
        return map_rect, cell_w, cell_h

    def _cell_center(self, row, col, map_rect, cell_w, cell_h):
        x = map_rect.left + (col + 0.5) * cell_w
        y = map_rect.top + (row + 0.5) * cell_h
        return x, y

    def _screen_to_cell(self, mouse_pos, map_rect, cell_w, cell_h):
        if not map_rect.collidepoint(mouse_pos):
            return None

        x, y = mouse_pos
        col = int((x - map_rect.left) / cell_w)
        row = int((y - map_rect.top) / cell_h)
        row = max(0, min(self.rows - 1, row))
        col = max(0, min(self.cols - 1, col))
        return row, col

    def _draw_grid(self, map_rect, cell_w, cell_h):
        block_a = (43, 52, 58)
        block_b = (36, 45, 50)
        road_line = (67, 82, 92)
        major_road = (88, 109, 122)

        pygame.draw.rect(self.screen, (25, 31, 35), map_rect, border_radius=10)

        for r in range(self.rows):
            for c in range(self.cols):
                rect = pygame.Rect(
                    map_rect.left + c * cell_w,
                    map_rect.top + r * cell_h,
                    cell_w + 1,
                    cell_h + 1,
                )
                color = block_a if (r + c) % 2 == 0 else block_b
                pygame.draw.rect(self.screen, color, rect)

        for r in range(self.rows + 1):
            y = map_rect.top + r * cell_h
            width = 2 if r % 5 == 0 else 1
            color = major_road if r % 5 == 0 else road_line
            pygame.draw.line(self.screen, color, (map_rect.left, y), (map_rect.right, y), width)

        for c in range(self.cols + 1):
            x = map_rect.left + c * cell_w
            width = 2 if c % 5 == 0 else 1
            color = major_road if c % 5 == 0 else road_line
            pygame.draw.line(self.screen, color, (x, map_rect.top), (x, map_rect.bottom), width)

        pygame.draw.rect(self.screen, (115, 140, 155), map_rect, 2, border_radius=10)

    def _draw_ride_start(self, pos, radius):
        x, y = int(pos[0]), int(pos[1])
        body = max(3, int(radius * 0.58))
        head = max(2, int(radius * 0.35))
        pygame.draw.circle(self.screen, self.palette["waiting"], (x, y + 1), body)
        pygame.draw.circle(self.screen, (255, 236, 170), (x, y - body), head)
        pygame.draw.circle(self.screen, (79, 57, 24), (x, y + 1), body, 1)

    def _draw_ride_end(self, pos, radius, emphasized=False):
        x, y = int(pos[0]), int(pos[1])
        color = self.palette["destination"]
        size = max(4, int(radius))
        pygame.draw.line(self.screen, color, (x - size, y - size), (x + size, y + size), 2)
        pygame.draw.line(self.screen, color, (x - size, y + size), (x + size, y - size), 2)
        if emphasized:
            pygame.draw.circle(self.screen, (199, 255, 213), (x, y), size + 4, 1)

    def _draw_car(self, x, y, radius, direction, state, car_id, show_label):
        base_color = self.palette["car_active"] if state == "dropoff" else self.palette["car"]
        border_color = (236, 252, 255)

        body_w = max(8, int(radius * 2.3))
        body_h = max(6, int(radius * 1.4))
        rect = pygame.Rect(int(x - body_w / 2), int(y - body_h / 2), body_w, body_h)
        pygame.draw.rect(self.screen, base_color, rect, border_radius=max(2, int(body_h * 0.25)))
        pygame.draw.rect(self.screen, border_color, rect, 1, border_radius=max(2, int(body_h * 0.25)))

        nose_offset = max(3, int(radius * 0.95))
        side = max(3, int(radius * 0.45))
        if direction == "up":
            points = [(x, y - nose_offset), (x - side, y - side), (x + side, y - side)]
        elif direction == "down":
            points = [(x, y + nose_offset), (x - side, y + side), (x + side, y + side)]
        elif direction == "left":
            points = [(x - nose_offset, y), (x - side, y - side), (x - side, y + side)]
        else:
            points = [(x + nose_offset, y), (x + side, y - side), (x + side, y + side)]

        pygame.draw.polygon(self.screen, base_color, points)
        pygame.draw.polygon(self.screen, border_color, points, 1)

        if state == "dropoff":
            pygame.draw.circle(self.screen, (178, 255, 198), (int(x), int(y)), radius + 5, 2)
        elif state == "waiting":
            pygame.draw.circle(self.screen, (245, 245, 245), (int(x), int(y)), radius + 3, 1)

        if show_label:
            label = self.small_font.render(str(car_id), True, self.palette["text_dark"])
            label_rect = label.get_rect(center=(int(x), int(y)))
            self.screen.blit(label, label_rect)

    def _draw_rides(self, state, map_rect, cell_w, cell_h):
        rides = state.get("rides", {})
        waiting = rides.get("waiting", [])
        assigned = rides.get("assigned", [])
        active = rides.get("active", [])
        completed = rides.get("completed", [])
        expired = rides.get("expired", [])

        waiting_cell_counts = {}

        for ride in waiting:
            key = (ride["start_r"], ride["start_c"])
            waiting_cell_counts[key] = waiting_cell_counts.get(key, 0) + 1

            start_pos = self._cell_center(ride["start_r"], ride["start_c"], map_rect, cell_w, cell_h)
            end_pos = self._cell_center(ride["end_r"], ride["end_c"], map_rect, cell_w, cell_h)
            pygame.draw.line(self.screen, (115, 138, 156), start_pos, end_pos, 1)
            marker_radius = max(4, int(min(cell_w, cell_h) * 0.2))
            self._draw_ride_start(start_pos, marker_radius)
            self._draw_ride_end(end_pos, marker_radius * 0.9)

        for ride in assigned:
            start_pos = self._cell_center(ride["start_r"], ride["start_c"], map_rect, cell_w, cell_h)
            end_pos = self._cell_center(ride["end_r"], ride["end_c"], map_rect, cell_w, cell_h)
            pygame.draw.line(self.screen, self.palette["assigned"], start_pos, end_pos, 2)
            marker_radius = max(4, int(min(cell_w, cell_h) * 0.18))
            self._draw_ride_start(start_pos, marker_radius)
            self._draw_ride_end(end_pos, marker_radius * 0.9)

        pulse = 2 + int((pygame.time.get_ticks() / 250) % 3)
        for ride in active:
            start_pos = self._cell_center(ride["start_r"], ride["start_c"], map_rect, cell_w, cell_h)
            end_pos = self._cell_center(ride["end_r"], ride["end_c"], map_rect, cell_w, cell_h)
            pygame.draw.line(self.screen, (126, 240, 168), start_pos, end_pos, 2)
            active_radius = max(4, int(min(cell_w, cell_h) * 0.2))
            self._draw_ride_end(end_pos, active_radius + pulse, emphasized=True)

        for ride in completed:
            end_pos = self._cell_center(ride["end_r"], ride["end_c"], map_rect, cell_w, cell_h)
            pygame.draw.circle(self.screen, (114, 132, 145), (int(end_pos[0]), int(end_pos[1])), max(2, int(min(cell_w, cell_h) * 0.10)))

        for ride in expired:
            start_pos = self._cell_center(ride["start_r"], ride["start_c"], map_rect, cell_w, cell_h)
            size = max(4, int(min(cell_w, cell_h) * 0.22))
            cx, cy = int(start_pos[0]), int(start_pos[1])
            pygame.draw.line(self.screen, (255, 90, 90), (cx - size, cy - size), (cx + size, cy + size), 2)
            pygame.draw.line(self.screen, (255, 90, 90), (cx - size, cy + size), (cx + size, cy - size), 2)

        for (row, col), count in waiting_cell_counts.items():
            if count <= 1:
                continue
            center = self._cell_center(row, col, map_rect, cell_w, cell_h)
            badge_radius = max(7, int(min(cell_w, cell_h) * 0.18))
            badge_pos = (int(center[0] + badge_radius), int(center[1] - badge_radius))
            pygame.draw.circle(self.screen, (19, 30, 42), badge_pos, badge_radius)
            pygame.draw.circle(self.screen, (255, 226, 156), badge_pos, badge_radius, 1)
            text = self.small_font.render(str(count), True, (232, 247, 255))
            text_rect = text.get_rect(center=badge_pos)
            self.screen.blit(text, text_rect)

    def _draw_vehicles(self, state, map_rect, cell_w, cell_h):
        vehicles = state.get("vehicles", [])
        grouped = {}
        for car in vehicles:
            key = (car["r"], car["c"])
            grouped.setdefault(key, []).append(car)

        for car in vehicles:
            if car.get("state") == "idle":
                continue
            start = self._cell_center(car["r"], car["c"], map_rect, cell_w, cell_h)
            target = self._cell_center(car["target_r"], car["target_c"], map_rect, cell_w, cell_h)
            if car.get("state") == "dropoff":
                pygame.draw.line(self.screen, (122, 230, 156), start, target, 2)
            else:
                pygame.draw.line(self.screen, (132, 164, 196), start, target, 1)

        car_radius = max(4, int(min(cell_w, cell_h) * 0.22))

        for (row, col), cars in grouped.items():
            center = self._cell_center(row, col, map_rect, cell_w, cell_h)
            count = len(cars)

            for idx, car in enumerate(cars):
                if count == 1:
                    px, py = center
                else:
                    angle = (2 * math.pi * idx) / count
                    offset = min(cell_w, cell_h) * 0.25
                    px = center[0] + math.cos(angle) * offset
                    py = center[1] + math.sin(angle) * offset

                dr = car["target_r"] - car["r"]
                dc = car["target_c"] - car["c"]
                if abs(dc) >= abs(dr):
                    direction = "right" if dc >= 0 else "left"
                else:
                    direction = "down" if dr >= 0 else "up"

                self._draw_car(
                    px,
                    py,
                    car_radius,
                    direction,
                    car.get("state", "idle"),
                    car["id"],
                    min(cell_w, cell_h) >= 24,
                )

            if count > 1:
                cluster_radius = car_radius + max(3, int(min(cell_w, cell_h) * 0.1))
                pygame.draw.circle(self.screen, (245, 245, 245), (int(center[0]), int(center[1])), cluster_radius, 1)
                badge = self.small_font.render(str(count), True, (245, 245, 245))
                badge_rect = badge.get_rect(center=(int(center[0]), int(center[1] - cluster_radius - 8)))
                self.screen.blit(badge, badge_rect)

        if self.selected_car_id is not None:
            selected = next((c for c in vehicles if c["id"] == self.selected_car_id), None)
            if selected:
                center = self._cell_center(selected["r"], selected["c"], map_rect, cell_w, cell_h)
                pygame.draw.circle(self.screen, (255, 255, 255), (int(center[0]), int(center[1])), car_radius + 7, 2)

    def _draw_messages(self, state, map_rect, cell_w, cell_h):
        for msg in state.get("messages", []):
            msg_x, msg_y = self._cell_center(msg["r"], msg["c"], map_rect, cell_w, cell_h)
            msg_y -= 24

            text_surface = self.small_font.render(msg["text"], True, msg["color"])
            text_rect = text_surface.get_rect(center=(int(msg_x), int(msg_y)))

            bg_rect = text_rect.inflate(10, 8)
            pygame.draw.rect(self.screen, (27, 35, 42), bg_rect, border_radius=4)
            pygame.draw.rect(self.screen, msg["color"], bg_rect, 1, border_radius=4)

            self.screen.blit(text_surface, text_rect)

    def _draw_panel(self, state):
        panel = self._panel_rect()
        stats = state.get("stats", {})
        rides = state.get("rides", {})

        pygame.draw.rect(self.screen, (18, 23, 27), panel)
        pygame.draw.line(self.screen, (56, 72, 80), (panel.left, 0), (panel.left, panel.bottom), 2)

        x = panel.left + 16
        y = 16

        title = self.title_font.render("Simulation Dashboard", True, (220, 240, 255))
        self.screen.blit(title, (x, y))
        y += 40

        time_text = f"Time: {state.get('current_step', 0)} / {state.get('total_time', 0)}"
        time_surface = self.font.render(time_text, True, (255, 255, 255))
        self.screen.blit(time_surface, (x, y))
        y += 28

        speed_text = f"Playback: {'PAUSED' if self.paused else 'PLAY'} | {self.speed_fps} step/s"
        speed_surface = self.small_font.render(speed_text, True, (163, 219, 255))
        self.screen.blit(speed_surface, (x, y))
        y += 24

        key_values = [
            ("Vehicles", stats.get("vehicles_total", 0)),
            ("Rides total", stats.get("rides_total", 0)),
            ("Waiting", stats.get("rides_waiting", 0)),
            ("Assigned", stats.get("rides_assigned", 0)),
            ("Active", stats.get("rides_active", 0)),
            ("Completed", stats.get("rides_completed", 0)),
            ("Expired", stats.get("rides_expired", 0)),
            ("Score", stats.get("current_score", state.get("score", 0))),
            ("Bonus hits", stats.get("bonus_count", state.get("bonus_count", 0))),
        ]

        for label, value in key_values:
            row_text = self.font.render(f"{label}: {value}", True, (225, 233, 240))
            self.screen.blit(row_text, (x, y))
            y += 24

        y += 10
        legend_title = self.font.render("Legend", True, (220, 240, 255))
        self.screen.blit(legend_title, (x, y))
        y += 26

        legends = [
            ("Car", self.palette["car"]),
            ("Waiting passenger", self.palette["waiting"]),
            ("Destination", self.palette["destination"]),
            ("Car on active ride", self.palette["car_active"]),
        ]

        for text, color in legends:
            pygame.draw.rect(self.screen, color, (x + 2, y + 2, 12, 12), border_radius=2)
            line = self.small_font.render(text, True, (224, 233, 241))
            self.screen.blit(line, (x + 24, y))
            y += 20

        y += 10
        controls = [
            "Controls",
            "SPACE: play/pause",
            "RIGHT/LEFT: step",
            "R or HOME: reset",
            "UP/DOWN: speed",
            "Mouse: select car/ride",
        ]
        for idx, line in enumerate(controls):
            font = self.font if idx == 0 else self.small_font
            color = (220, 240, 255) if idx == 0 else (191, 214, 228)
            surf = font.render(line, True, color)
            self.screen.blit(surf, (x, y))
            y += 22 if idx == 0 else 18

        y += 8
        vehicles = state.get("vehicles", [])
        rides_lookup = {
            ride["id"]: ride
            for status_name in ["waiting", "assigned", "active", "completed", "expired"]
            for ride in rides.get(status_name, [])
        }

        if self.selected_car_id is not None:
            selected_car = next((car for car in vehicles if car["id"] == self.selected_car_id), None)
            if selected_car:
                heading = self.font.render(f"Car #{selected_car['id']}", True, (255, 244, 204))
                self.screen.blit(heading, (x, y))
                y += 24

                details = [
                    f"Pos: ({selected_car['r']}, {selected_car['c']})",
                    f"Target: ({selected_car['target_r']}, {selected_car['target_c']})",
                    f"State: {selected_car['state']}",
                    f"Assigned rides: {selected_car.get('assigned_count', 0)}",
                ]
                for line in details:
                    surf = self.small_font.render(line, True, (238, 236, 220))
                    self.screen.blit(surf, (x, y))
                    y += 18

        if self.selected_ride_id is not None:
            selected_ride = rides_lookup.get(self.selected_ride_id)
            if selected_ride:
                y += 10
                heading = self.font.render(f"Ride #{selected_ride['id']}", True, (204, 255, 214))
                self.screen.blit(heading, (x, y))
                y += 24

                details = [
                    f"Start: ({selected_ride['start_r']}, {selected_ride['start_c']})",
                    f"Finish: ({selected_ride['end_r']}, {selected_ride['end_c']})",
                    f"Earliest: {selected_ride['earliest']}",
                    f"Latest: {selected_ride['latest']}",
                    f"Distance: {selected_ride['distance']}",
                    f"Status: {selected_ride['status']}",
                ]
                for line in details:
                    surf = self.small_font.render(line, True, (226, 255, 231))
                    self.screen.blit(surf, (x, y))
                    y += 18

    def _select_from_click(self, state, row, col):
        vehicles = state.get("vehicles", [])
        rides = state.get("rides", {})

        cars_here = [car for car in vehicles if car["r"] == row and car["c"] == col]
        if cars_here:
            self.selected_car_id = cars_here[0]["id"]
        else:
            self.selected_car_id = None

        candidate_rides = []
        for status_name in ["waiting", "assigned", "active", "completed", "expired"]:
            for ride in rides.get(status_name, []):
                if (ride["start_r"], ride["start_c"]) == (row, col) or (ride["end_r"], ride["end_c"]) == (row, col):
                    candidate_rides.append(ride)

        if candidate_rides:
            priority = {
                "waiting": 0,
                "assigned": 1,
                "active": 2,
                "expired": 3,
                "completed": 4,
            }
            candidate_rides.sort(key=lambda r: priority.get(r["status"], 99))
            self.selected_ride_id = candidate_rides[0]["id"]
        else:
            self.selected_ride_id = None

    def render(self, state):
        user_action = None

        map_rect, cell_w, cell_h = self._cell_geometry(state)

        all_ride_ids = {
            ride["id"]
            for status_name in ["waiting", "assigned", "active", "completed", "expired"]
            for ride in state.get("rides", {}).get(status_name, [])
        }
        if self.selected_ride_id is not None and self.selected_ride_id not in all_ride_ids:
            self.selected_ride_id = None

        vehicle_ids = {car["id"] for car in state.get("vehicles", [])}
        if self.selected_car_id is not None and self.selected_car_id not in vehicle_ids:
            self.selected_car_id = None

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_RIGHT:
                    user_action = "FORWARD"
                elif event.key == pygame.K_LEFT:
                    user_action = "BACKWARD"
                elif event.key == pygame.K_SPACE:
                    self.paused = not self.paused
                elif event.key == pygame.K_r or event.key == pygame.K_HOME:
                    user_action = "RESET"
                elif event.key == pygame.K_UP:
                    self.speed_fps = min(60, self.speed_fps + 1)
                elif event.key == pygame.K_DOWN:
                    self.speed_fps = max(1, self.speed_fps - 1)
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                clicked_cell = self._screen_to_cell(event.pos, map_rect, cell_w, cell_h)
                if clicked_cell is not None:
                    row, col = clicked_cell
                    self._select_from_click(state, row, col)

        if not self.paused and user_action is None:
            now = pygame.time.get_ticks()
            step_interval = max(1, int(1000 / self.speed_fps))
            if now - self.last_auto_step_ms >= step_interval:
                user_action = "FORWARD"
                self.last_auto_step_ms = now

        self.screen.fill((11, 16, 20))

        self._draw_grid(map_rect, cell_w, cell_h)
        self._draw_rides(state, map_rect, cell_w, cell_h)
        self._draw_vehicles(state, map_rect, cell_w, cell_h)
        self._draw_messages(state, map_rect, cell_w, cell_h)
        self._draw_panel(state)

        pygame.display.flip()
        self.clock.tick(60)

        return user_action