import arcade
import math
import random

from pyglet.graphics import Batch
from arcade.particles import FadeParticle, Emitter, EmitBurst, EmitInterval, EmitMaintainCount
from arcade.gui import UIManager, UIFlatButton, UITextureButton, UILabel, UIInputText, UITextArea, UISlider, UIDropdown, \
    UIMessageBox
from arcade.gui.widgets.layout import UIAnchorLayout, UIBoxLayout

TILE_SCALING = 1.0
SCREEN_WIDTH = 1280
SCREEN_HEIGHT = 720

RANDOM_LOOT = ['heal', 'bomb']
CHANCE = [70, 30]

SPARK_TEX = [
    arcade.make_soft_circle_texture(12, arcade.color.NEON_GREEN),
    arcade.make_soft_circle_texture(12, arcade.color.ELECTRIC_LIME),
    arcade.make_soft_circle_texture(12, arcade.color.ELECTRIC_CYAN),
    arcade.make_soft_circle_texture(12, arcade.color.SPRING_GREEN),
]
SMOKE_TEX = arcade.make_soft_circle_texture(20, arcade.color.NEON_GREEN, 255, 80)
PUFF_TEX = arcade.make_soft_circle_texture(12, arcade.color.WHITE, 255, 50)


def gravity_drag(p):  # Для искр: чуть вниз и затухание скорости
    p.change_y += -0.03
    p.change_x *= 0.92
    p.change_y *= 0.92


def smoke_mutator(p):  # Дым раздувается и плавно исчезает
    p.scale_x *= 1.02
    p.scale_y *= 1.02
    p.alpha = max(0, p.alpha - 2)


# Фабрики эмиттеров (возвращают готовый Emitter)
def make_explosion(x, y, count=80):
    # Разовый взрыв с искрами во все стороны
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitBurst(count),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=random.choice(SPARK_TEX),
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 9.0),
            lifetime=random.uniform(0.5, 1.1),
            start_alpha=255, end_alpha=0,
            scale=random.uniform(0.35, 0.6),
            mutation_callback=gravity_drag,
        ),
    )


def make_ring(x, y, count=40, radius=5.0):
    # Кольцо искр (векторы направлены по окружности)
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitBurst(count),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=random.choice(SPARK_TEX),
            change_xy=arcade.math.rand_on_circle((0.0, 0.0), radius),
            lifetime=random.uniform(0.8, 1.4),
            start_alpha=255, end_alpha=0,
            scale=random.uniform(0.4, 0.7),
            mutation_callback=gravity_drag,
        ),
    )


def make_fountain(x, y):
    # Фонтанчик: равномерный «дождик» вверх, бесконечно
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitInterval(0.02),  # Непрерывный поток
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=PUFF_TEX,
            change_xy=(random.uniform(-0.8, 0.8), random.uniform(4.0, 6.0)),
            lifetime=random.uniform(0.8, 1.6),
            start_alpha=240, end_alpha=0,
            scale=random.uniform(0.4, 0.8),
            mutation_callback=gravity_drag,
        ),
    )


def make_smoke_puff(x, y):
    # Короткий «пых» дыма: медленно плывёт и распухает
    return Emitter(
        center_xy=(x, y),
        emit_controller=EmitBurst(12),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=SMOKE_TEX,
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 0.6),
            lifetime=random.uniform(1.5, 2.5),
            start_alpha=200, end_alpha=0,
            scale=random.uniform(0.6, 0.9),
            mutation_callback=smoke_mutator,
        ),
    )


def make_trail(attached_sprite, maintain=60):
    # «След за объектом»: поддерживаем постоянное число частиц
    emit = Emitter(
        center_xy=(attached_sprite.center_x, attached_sprite.center_y),
        emit_controller=EmitMaintainCount(maintain),
        particle_factory=lambda e: FadeParticle(
            filename_or_texture=random.choice(SPARK_TEX),
            change_xy=arcade.math.rand_in_circle((0.0, 0.0), 1.6),
            lifetime=random.uniform(0.35, 0.9),
            start_alpha=220, end_alpha=0,
            scale=random.uniform(0.25, 0.9),
        ),
    )
    # Хитрость: каждое обновление будем прижимать центр к спрайту (см. ниже)
    emit._attached = attached_sprite
    return emit


class MenuView(arcade.View):
    def __init__(self):
        super().__init__()
        self.background_color = arcade.color.BLACK  # Фон для меню

        self.manager = UIManager()
        self.manager.enable()

        self.anchor_layout = UIAnchorLayout()  # Центрирует виджеты
        self.box_layout = UIBoxLayout(vertical=True, space_between=10)

        self.setup_widgets()

        self.anchor_layout.add(self.box_layout)  # Box в anchor
        self.manager.add(self.anchor_layout)

    def on_draw(self):
        self.clear()
        self.manager.draw()

    def setup_widgets(self):
        # Здесь добавим ВСЕ виджеты — по порядку!
        label = UILabel(text="ИГРА",
                        font_name='Bahnschrift',
                        font_size=100,
                        text_color=arcade.color.WHITE,
                        width=300,
                        align="center")
        self.box_layout.add(label)

        flat_button = UIFlatButton(text="ИГРАТЬ", width=400, height=80)
        flat_button.style['normal'].fill_color = arcade.color.LIGHT_GREEN
        flat_button.style['normal'].fill_color = arcade.color.GREEN
        flat_button.style['normal'].font_color = arcade.color.BLACK
        flat_button.style['normal'].border_color = arcade.color.NEON_GREEN
        flat_button.style['normal'].border_width = 2
        flat_button.on_click = self.switch
        self.box_layout.add(flat_button)

    def switch(self, event):
        game_view = GameView()  # Создаём игровой вид
        self.window.show_view(game_view)  # Переключаем

    def on_mouse_press(self, x, y, button, modifiers):
        pass


class Bullet(arcade.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y,
                 speed=800, damage=50, owner="player"):
        super().__init__()
        if owner == "player":
            self.texture = arcade.load_texture("laser_2.png")
            self.scale = 0.2
        else:
            self.texture = arcade.load_texture("laser_1.png")
            self.scale = 0.4

        self.center_x = start_x
        self.center_y = start_y
        self.speed = speed
        self.damage = damage
        self.owner = owner

        # Рассчитываем направление
        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)

        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.angle = math.degrees(-angle)

    def update(self, delta_time):
        if (self.center_x < 0 or self.center_x > 4000 or
                self.center_y < 0 or self.center_y > 4000):
            self.remove_from_sprite_lists()

        self.center_x += self.change_x * delta_time
        self.center_y += self.change_y * delta_time


class Enemy(arcade.Sprite):
    def __init__(self, game_view, player, x, y):
        super().__init__()
        self.game_view = game_view
        self.health = 100
        self.texture = arcade.load_texture("ufoGreen.png")
        self.scale = 1.5
        self.pulse_direction = 10
        self.speed = 1.5
        self.player = player
        self.center_x = x
        self.center_y = y
        self.bullet_list = arcade.SpriteList()

        self.timer = 0
        self.interval = random.uniform(0.5, 4.0)
        self.vision_timer = 0
        self.can_see = False

        self.physics_engine = arcade.PhysicsEngineSimple(
            self,
            [self.game_view.collision_list,
             self.game_view.doors_list]
        )

    def shoot(self):
        # Передаем координаты в Bullet
        bullet = Bullet(
            self.center_x,
            self.center_y,
            self.player.center_x, self.player.center_y,
            owner='enemy'
        )
        self.bullet_list.append(bullet)

    def update(self, delta_time):
        self.bullet_list.update()

        self.timer += delta_time
        self.vision_timer += delta_time

        for bullet in self.bullet_list:
            if arcade.check_for_collision_with_list(bullet, self.game_view.collision_list):
                bullet.remove_from_sprite_lists()
                continue

            if arcade.check_for_collision(bullet, self.player):
                bullet.remove_from_sprite_lists()
                self.game_view.player_hp -= bullet.damage

        # Эффект пульсации
        new_width = self.width + self.pulse_direction * 1.5 * delta_time
        if new_width > 70 or new_width < 58:
            self.pulse_direction *= -1
            new_width = max(58, min(70, new_width))
        self.width = new_width
        self.height = new_width

        dx = self.player.center_x - self.center_x
        dy = self.player.center_y - self.center_y
        distance = math.sqrt(dx * dx + dy * dy)

        # --- ЛОГИКА ЗРЕНИЯ ---
        if self.vision_timer > 0.2:
            self.vision_timer = 0
            if distance < 500:  # Радиус обнаружения
                # 2. Проверяем, нет ли стен между центром врага и центром игрока
                # Используем встроенную функцию arcade
                self.can_see = arcade.has_line_of_sight(
                    self.player.position,
                    self.position,
                    self.game_view.collision_list,
                    check_resolution=16
                )
            else:
                self.can_see = False

        if self.can_see:
            # Двигается к игроку
            if distance > 10:
                self.change_x = (dx / distance) * self.speed
                self.change_y = (dy / distance) * self.speed

            if self.timer >= self.interval:
                self.shoot()
                self.timer = 0
                self.interval = random.uniform(0.5, 4.0)
        else:
            self.change_x = 0
            self.change_y = 0

        self.physics_engine.update()


class Key(arcade.Sprite):
    def __init__(self):
        super().__init__()
        self.texture = arcade.load_texture("hud_keyGreen.png")
        self.scale = 2
        self.center_x = 100
        self.center_y = 900


class Loot(arcade.Sprite):
    def __init__(self, name, x, y, game_w):
        super().__init__()
        self.game_w = game_w
        self.name = name
        if self.name == 'heal':
            self.texture = arcade.load_texture("hud_heartFull.png")
            self.center_x = x
            self.center_y = y
            self.scale = 0.5

        if self.name == 'bomb':
            self.texture = arcade.load_texture("bomb.png")
            self.center_x = x
            self.center_y = y
            self.scale = 1

    def update(self, delta_time):
        if self.name == 'heal':
            if arcade.check_for_collision(self.game_w.player_sprite, self):
                self.kill()
                self.game_w.player_hp += 30

        if self.name == 'bomb':
            if arcade.check_for_collision(self.game_w.player_sprite, self):
                self.kill()
                self.game_w.count_bomb += 1


class Bomb(arcade.Sprite):
    def __init__(self, start_x, start_y, target_x, target_y, game_w,
                 speed=300, damage=500):
        super().__init__()
        self.texture = arcade.load_texture("bomb.png")
        self.scale = 0.5
        self.game_w = game_w
        self.center_x = start_x
        self.center_y = start_y
        self.speed = speed
        self.damage = damage
        self.timer_boom = 0

        x_diff = target_x - start_x
        y_diff = target_y - start_y
        angle = math.atan2(y_diff, x_diff)

        self.change_x = math.cos(angle) * speed
        self.change_y = math.sin(angle) * speed
        self.angle = math.degrees(-angle)

    def update(self, delta_time):
        if (self.center_x < 0 or self.center_x > 4000 or
                self.center_y < 0 or self.center_y > 4000):
            self.remove_from_sprite_lists()

        self.timer_boom += delta_time

        self.center_x += self.change_x * delta_time
        hit_list_x = arcade.check_for_collision_with_list(self, self.game_w.collision_list)
        if hit_list_x:
            for wall in hit_list_x:
                if self.change_x > 0:
                    self.right = wall.left
                elif self.change_x < 0:
                    self.left = wall.right

            self.change_x *= -1

        self.center_y += self.change_y * delta_time
        hit_list_y = arcade.check_for_collision_with_list(self, self.game_w.collision_list)

        if hit_list_y:
            for wall in hit_list_y:
                if self.change_y > 0:
                    self.top = wall.bottom
                elif self.change_y < 0:
                    self.bottom = wall.top

            self.change_y *= -1

        if self.timer_boom > 0.8:
            self.booms()

    def booms(self):
        boom = Booms(self.center_x, self.center_y, self.game_w, self)
        self.game_w.boom_list.append(boom)

        self.kill()


class Booms(arcade.Sprite):
    def __init__(self, x, y, game, bomb):
        super().__init__()
        self.texture = arcade.make_soft_circle_texture(64, arcade.color.NEON_GREEN)
        self.center_x = x
        self.center_y = y
        self.scale = 1
        self.game_w = game
        self.bomb = bomb

    def update(self, delta_time):
        self.width += 18
        self.height += 18
        self.alpha -= 10
        self.game_w.emitters.append(make_smoke_puff(self.center_x, self.center_y))
        hit_list_boom = arcade.check_for_collision_with_list(self, self.game_w.enemy_list)
        if hit_list_boom:
            for en in hit_list_boom:
                en.health -= self.bomb.damage
                if en.health <= 0:
                    en.kill()
        if self.width > 400 or self.alpha <= 0:
            self.kill()


class GameView(arcade.View):
    def __init__(self):
        super().__init__()
        # Здесь спрайты, физика
        self.player_speed = 300
        self.player_hp = 100000
        self.count_bomb = 0
        self.keys_pressed = set()
        self.close = True
        self.emitters = []
        self.fountain = None
        self.trail = None

        self.world_camera = arcade.camera.Camera2D()  # Камера для игрового мира
        self.gui_camera = arcade.camera.Camera2D()
        self.world_camera.zoom = 2

        # Инициализируем списки спрайтов

        self.player_list = arcade.SpriteList()
        self.wall_list = arcade.SpriteList()  # Сюда попадёт слой Collision!
        self.enemy_list = arcade.SpriteList()
        self.bullet_list = arcade.SpriteList()
        self.keys = arcade.SpriteList()
        self.loot_list = arcade.SpriteList()
        self.bomb_list = arcade.SpriteList()
        self.boom_list = arcade.SpriteList()

        # ===== ВОЛШЕБСТВО ЗАГРУЗКИ КАРТЫ! (Почти без магии.) =====
        map_name = "testik.tmx"
        tile_map = arcade.load_tilemap(map_name, scaling=TILE_SCALING)

        # --- Достаём слои из карты как спрайт-листы ---
        self.wall_list = tile_map.sprite_lists["walls"]
        enemy_list_0 = tile_map.sprite_lists["enemy"]
        self.chests_list = tile_map.sprite_lists["chests"]
        self.doors_list = tile_map.sprite_lists["doors"]
        self.barrel_list = tile_map.sprite_lists["barrel"]
        # Слой "exit" (выходы с уровня) — красота!
        # self.exit_list = tile_map.sprite_lists["exit"]
        self.collision_list = tile_map.sprite_lists["collision"]
        self.collision_list.use_spatial_hashing = True
        self.collision_list.enable_spatial_hashing()
        # --- Создаём игрока ---
        self.player_sprite = arcade.Sprite("p1_stand.png",
                                           0.5)

        self.world_width = int(tile_map.width * tile_map.tile_width * TILE_SCALING)
        self.world_height = int(tile_map.height * tile_map.tile_height * TILE_SCALING)

        # Ставим игрока куда-нибудь на землю (посмотрите в Tiled, где у вас земля!)
        self.player_sprite.center_x = 128  # Примерные координаты
        self.player_sprite.center_y = 256  # Примерные координаты
        self.player_list.append(self.player_sprite)

        # --- Физический движок ---
        # Используем PhysicsEngineSimple, который знаем и любим
        self.physics_engine = arcade.PhysicsEngineSimple(
            self.player_sprite, [self.collision_list, self.doors_list]
        )

        for enemy_sprite in enemy_list_0:
            enemy = Enemy(
                game_view=self,
                player=self.player_sprite,
                x=enemy_sprite.center_x,
                y=enemy_sprite.center_y
            )
            self.enemy_list.append(enemy)

    def on_resize(self, width: int, height: int):
        self.world_camera.viewport = (0, 0, width, height)
        self.gui_camera.viewport = (0, 0, width, height)
        self.gui_camera.projection = (0, width, 0, height)

    def on_draw(self):
        self.clear()

        self.world_camera.use()
        self.wall_list.draw()
        self.chests_list.draw()
        # self.exit_list.draw()
        if self.close:
            self.doors_list.draw()
        self.player_list.draw()
        self.enemy_list.draw()
        self.bullet_list.draw()
        self.loot_list.draw()
        self.barrel_list.draw()
        self.bomb_list.draw()
        self.boom_list.draw()

        for e in self.emitters:
            e.draw()

        for enemy in self.enemy_list:
            enemy.bullet_list.draw()

        self.gui_camera.use()
        arcade.draw_text(
            f"Player: ({int(self.player_sprite.center_x)}, {int(self.player_sprite.center_y)})",
            10, 580,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Player hp: {self.player_hp}",
            10, 280,
            arcade.color.WHITE, 16
        )
        arcade.draw_text(
            f"Bombs: {self.count_bomb}",
            10, 400,
            arcade.color.WHITE, 16
        )
        # хпбар
        self.bar = max(0, self.player_hp / 100000)
        arcade.draw_lbwh_rectangle_filled(9, 99, 402, 22, arcade.color.WHITE)
        arcade.draw_lbwh_rectangle_filled(10, 100, 400 * self.bar, 20, arcade.color.RED)

        # предметы
        self.keys.draw()

    def on_update(self, dt: float):
        # Обновляем физику
        self.player_sprite.change_x = 0
        self.player_sprite.change_y = 0

        self.enemy_list.update(dt)
        self.bullet_list.update(dt)
        self.loot_list.update(dt)
        self.bomb_list.update(dt)
        self.boom_list.update(dt)

        if arcade.key.A in self.keys_pressed:
            self.player_sprite.change_x = -self.player_speed * dt
        if arcade.key.D in self.keys_pressed:
            self.player_sprite.change_x = self.player_speed * dt
        if arcade.key.W in self.keys_pressed:
            self.player_sprite.change_y = self.player_speed * dt
        if arcade.key.S in self.keys_pressed:
            self.player_sprite.change_y = -self.player_speed * dt

        if self.player_sprite.change_x != 0 and self.player_sprite.change_y != 0:
            self.player_sprite.change_x *= 0.7071
            self.player_sprite.change_y *= 0.7071

        if self.trail:
            self.trail.center_x = self.player_sprite.center_x
            self.trail.center_y = self.player_sprite.center_y

        # Обновляем эмиттеры и чистим «умершие»
        emitters_copy = self.emitters.copy()  # Защищаемся от мутаций списка
        for e in emitters_copy:
            e.update(dt)
        for e in emitters_copy:
            if e.can_reap():  # Готов к уборке?
                self.emitters.remove(e)

        for bullet in self.bullet_list:
            enemies_hit_list = arcade.check_for_collision_with_list(bullet, self.enemy_list)
            barrel_hit = arcade.check_for_collision_with_list(bullet, self.barrel_list)

            if arcade.check_for_collision_with_lists(bullet, [self.collision_list, self.doors_list]):
                bullet.remove_from_sprite_lists()
                continue

            # Если лазер попал в зомби, удаляем и лазер, и зомби
            if enemies_hit_list:
                bullet.remove_from_sprite_lists()
                for enemy in enemies_hit_list:
                    enemy.health -= bullet.damage
                    if enemy.health <= 0:
                        enemy.remove_from_sprite_lists()
                        self.emitters.append(make_explosion(enemy.center_x, enemy.center_y))

            # если попал в ящик
            if barrel_hit:
                bullet.remove_from_sprite_lists()
                for bar in barrel_hit[:]:
                    item = random.choices(RANDOM_LOOT, weights=CHANCE, k=1)[0]
                    loot = Loot(item,
                                bar.center_x,
                                bar.center_y,
                                self)
                    bar.remove_from_sprite_lists()
                    self.loot_list.append(loot)

        if self.close:
            if arcade.check_for_collision_with_list(self.player_sprite, self.chests_list):
                key = Key()
                self.keys.append(key)
                self.close = False
                for door in self.doors_list[:]:
                    door.remove_from_sprite_lists()

            # если игрок коснулся бочки
        if arcade.check_for_collision_with_list(self.player_sprite, self.barrel_list):
            hit = arcade.check_for_collision_with_list(self.player_sprite, self.barrel_list)
            for barrel in hit[:]:
                item = random.choices(RANDOM_LOOT, weights=CHANCE, k=1)[0]
                loot = Loot(item,
                            barrel.center_x,
                            barrel.center_y,
                            self)
                barrel.remove_from_sprite_lists()
                self.loot_list.append(loot)

        self.physics_engine.update()

        # камера в мире
        view_w = self.world_camera.viewport_width / self.world_camera.zoom
        view_h = self.world_camera.viewport_height / self.world_camera.zoom

        half_w = view_w / 2
        half_h = view_h / 2

        target_x = self.player_sprite.center_x
        target_y = self.player_sprite.center_y

        cam_x = max(half_w, min(self.world_width - half_w, target_x))
        cam_y = max(half_h, min(self.world_height - half_h, target_y))

        self.world_camera.position = arcade.math.lerp_2d(
            self.world_camera.position,
            (cam_x, cam_y),
            0.15  # Плавность
        )

        self.gui_camera.position = (
            self.gui_camera.viewport_width / 2,
            self.gui_camera.viewport_height / 2
        )

    def on_mouse_press(self, x, y, button, mod):
        """Выстрел по клику мыши"""
        # ПРЕОБРАЗУЕМ экранные координаты мыши в мировые!
        world_point = self.world_camera.unproject((x, y))
        world_x = world_point.x
        world_y = world_point.y
        if button == arcade.MOUSE_BUTTON_LEFT:
            bullet = Bullet(
                self.player_sprite.center_x,
                self.player_sprite.center_y,
                world_x, world_y,
            )
            self.bullet_list.append(bullet)
        if self.count_bomb > 0:
            if button == arcade.MOUSE_BUTTON_RIGHT:
                bomb = Bomb(
                    self.player_sprite.center_x,
                    self.player_sprite.center_y,
                    world_x, world_y,
                    self
                )
                self.bomb_list.append(bomb)
                # self.count_bomb -= 1

    def on_key_press(self, key, modifiers):
        if key == arcade.key.ESCAPE:
            pause_view = PauseView(self)  # Передаём текущий вид, чтобы вернуться
            self.window.show_view(pause_view)
        # Другие клавиши для движения.
        self.keys_pressed.add(key)

        if key == arcade.key.C:
            self.emitters.clear()
            self.fountain = None
            self.trail = None

        if key == arcade.key.V:
            if self.trail:
                self.emitters.remove(self.trail)
                self.trail = None
            else:
                self.trail = make_trail(self.player_sprite)
                self.emitters.append(self.trail)

    def on_key_release(self, key, modifiers):
        if key in self.keys_pressed:
            self.keys_pressed.remove(key)


class PauseView(arcade.View):
    def __init__(self, game_view):
        super().__init__()
        self.game_view = game_view  # Сохраняем, чтобы вернуться
        self.batch = Batch()
        self.pause_text = arcade.Text("Пауза", self.window.width / 2, self.window.height / 2,
                                      arcade.color.WHITE, font_size=40, anchor_x="center", batch=self.batch)
        self.space_text = arcade.Text("Нажми SPACE, чтобы продолжить", self.window.width / 2,
                                      self.window.height / 2 - 50,
                                      arcade.color.WHITE, font_size=20, anchor_x="center", batch=self.batch)

    def on_draw(self):
        self.clear()
        self.batch.draw()

    def on_key_press(self, key, modifiers):
        if key == arcade.key.SPACE:
            self.window.show_view(self.game_view)  # Возвращаемся в игру


def main():
    window = arcade.Window(width=1920,
                           height=1080,
                           resizable=False
                           )
    menu_view = MenuView()
    window.show_view(menu_view)
    arcade.run()


if __name__ == "__main__":
    main()

