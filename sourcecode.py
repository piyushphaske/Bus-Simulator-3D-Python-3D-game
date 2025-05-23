from direct.showbase.ShowBase import ShowBase
from direct.showbase.ShowBaseGlobal import aspect2d
from direct.task import Task
from panda3d.core import TexturePool, NodePath, Vec3, CollisionRay, CollisionNode, CollisionTraverser, \
    CollisionHandlerQueue, BitMask32, TextureStage, Material, load_prc_file_data, CollisionSphere, \
    CollisionHandlerPusher, Point3, CollisionBox, TextureAttrib, AudioManager
from direct.interval.SoundInterval import SoundInterval
import pygame
from pyexpat import model
from panda3d.core import NodePath, TextNode
from panda3d.core import Texture, TextureStage
class Car(ShowBase):
    def __init__(self):
        super().__init__()



        #set camera position
        self.cam.setPos(0, 15, -50)
        #set camera lookangle
        self.cam.lookAt(0, 0, 0)



        # Load city model
        self.model1 = self.loader.loadModel("/c/Users/Piyush/PycharmProjects/pythonProject5/city.bam")
        self.model1.findAllMatches("/c/Users/Piyush/PycharmProjects/pythonProject7/polycity.bam")
        #load bus model
        self.model4 = self.loader.loadModel("/c/Users/Piyush/PycharmProjects/pythonProject5/acbus.bam")

        # Apply city textures
        self.texture1 = TexturePool.loadTexture("/c/Users/Piyush/PycharmProjects/pythonProject5/textures/bricks.tif")
        #apply bus texture
        self.texture4 = TexturePool.loadTexture("/c/Users/Piyush/PycharmProjects/pythonProject5/textures/bustexture.jpg")

        self.roughness_texture = TexturePool.loadTexture("/c/Users/Piyush/PycharmProjects/pythonProject5/textures/roof 2.jpg")

        def apply_texture(model_path, texture, texture_stage=None):
            for node in model_path.findAllMatches("/+GeomNode"):
                geom_node = node.node()
                for geom in geom_node.modifiers.getGlobalData():
                    state = geom.getRenderState()
                    if texture_stage:
                        state = state.addSimpleAttrib(texture_stage, texture)
                    else:
                        state = state.addSimpleAttrib(TextureAttrib.getClassSimple(), texture)
                    geom.setRenderState(state)
        #apply roughness
        roughness_stage = TextureStage("roughness")

        #find model to apply roughness
        #building_path = self.model1.find("/c/Users/Piyush/PycharmProjects/pythonProject7/polycity.bam")
        #apply_texture(building_path, self.texture1)  # Apply the diffuse texture
        #apply_texture(building_path, self.roughness_texture, roughness_stage)  # Apply the roughness texture
        #render textures
        self.model1.setTexture(self.texture1)
        self.model4.setTexture(self.texture4)

        # Reparent models to the scene graph
        self.model1.reparentTo(self.render)
        self.model4.reparentTo(self.model1)

        # Position models relative to each other
        self.model1.setPos(0, 0, 0)
        self.model4.setScale(50,50,50)
        self.model4.setPos(15, 5, -1.5)

        # Car speed and direction
        self.car_speed = 5
        self.direction = Vec3(1, 0, 0)

        #lateral direction and turn speed
        self.lateral_direction = Vec3(0, 0, 0)
        self.turn_speed = 0

        # Camera settings
        #self.camera_distance = 20  # Adjust this value to change the distance between the camera and the bus
        #self.camera_height = 5  # Adjust this value to change the height of the camera

        # Setup collision picker for the camera
        self.setup_picker()

        #initislise pygame
        pygame.init()

        # Initialize pygame mixer for engine sound
        pygame.mixer.init()

        self.audio_manager = AudioManager.createAudioManager()

        # Load background music
        self.background_music = self.loader.loadSfx("/c/Users/Piyush/PycharmProjects/pythonProject7/citysound.ogg")

        self.background_music.setLoop(True)
        self.background_music.setVolume(20)
        self.background_music.play()

        # Load horn sound
        self.horn_sound = self.loader.loadSfx("/c/Users/Piyush/PycharmProjects/pythonProject7/horn.ogg")

        # load music system
        self.musicsystem_sound = self.loader.loadSfx("/c/Users/Piyush/PycharmProjects/pythonProject7/tokyodrift.ogg")

        # Load engine sound
        self.engine_sound = self.loader.loadSfx("/c/Users/Piyush/PycharmProjects/pythonProject7/revving.ogg")
        # Load the roughness texture
        #roughness_texture = TexturePool.loadTexture("/c/Users/Piyush/PycharmProjects/pythonProject5/download(4).png")

        # Create a new texture stage for the roughness texture
        roughness_stage = TextureStage("roughness")

        # Set the texture and texture stage for the model
        #model.setTexture(roughness_stage, roughness_texture)

        # Create a new material
        material = Material()

        # Set the material properties (e.g., roughness)
        material.setRoughness(1.0)  # Adjust the value as needed

        # Apply the material to the model
        #model.setMaterial(material)

        # Add task to drive the car and update the camera
        self.taskMgr.add(self.drive_car, "drive_car")

        # Accept keyboard input
        self.accept("q", self.accelerate)
        self.accept("q-up", self.stop_acceleration)
        self.accept("e", self.reverse)
        self.accept("e-up", self.stop_acceleration)
        self.accept("d", self.turn_left)
        self.accept("d-up", self.stop_turning)
        self.accept("a", self.turn_right)
        self.accept("a-up", self.stop_turning)
        self.accept("s", self.move_left)
        self.accept("s-up", self.stop_lateral_movement)
        self.accept("w", self.move_right)
        self.accept("w-up", self.stop_lateral_movement)

        # Start background music
        #self.background_music.play()

        # Add event for horn sound
        self.accept("h", self.play_horn)

        #add event for music system
        self.accept("f", self.music_system)

        # Add event for background music toggle
        #self.accept("m", self.toggle_background_music)

        self.building_collision_node = self.model1.attachNewNode(CollisionNode("building_collision"))
        self.building_collision_node.node().addSolid(
            CollisionBox(Point3(-200, -200, 0), Point3(200, 200, 100)))  # Adjust the dimensions as needed

        # Create a collision sphere for the bus model
        self.bus_collision_sphere = self.model4.attachNewNode(CollisionNode("bus_collision_sphere"))
        self.bus_collision_sphere.node().addSolid(CollisionSphere(0, 0, 0, 5))  # Adjust the radius as needed

        # Create a collision traverser and handler
        self.collision_traverser = CollisionTraverser()
        self.collision_handler = CollisionHandlerPusher()
        self.collision_handler.setHorizontal(True)  # Allow horizontal collisions

        # Add the collision sphere to the traverser and handler
        self.collision_traverser.addCollider(self.bus_collision_sphere, self.collision_handler)
        self.collision_traverser.addCollider(self.building_collision_node, self.collision_handler)

        # Traverse the scene to detect collisions
        self.collision_traverser.showCollisions(self.render)
        self.collision_traverser.addCollider(self.building_collision_node, self.collision_handler)

    def setup_picker(self):

        #setup collision handler

        self.picker = CollisionTraverser()
        self.pickerQueue = CollisionHandlerQueue()
        self.pickerNode = CollisionNode("pickerRay")
        self.pickerNP = self.cam.attachNewNode(self.pickerNode)
        self.pickerNode.setFromCollideMask(BitMask32.bit(1))
        self.pickerRay = CollisionRay()
        self.pickerNode.addSolid(self.pickerRay)
        self.picker.addCollider(self.pickerNP, self.pickerQueue)

    def drive_car(self, task):
        # Get the current position and heading of the car
        current_pos = self.model4.getPos(self.model1)
        current_hpr = self.model4.getHpr(self.model1)

        # Move the car based on keyboard input
        new_pos = current_pos + Vec3(self.car_speed * self.direction.getX(), self.car_speed * self.direction.getY(),
                                     self.car_speed * self.lateral_direction.getZ())
        self.model4.setPos(self.model1, new_pos)
        self.model4.setHpr(self.model1, current_hpr + Vec3(0, 0, self.turn_speed))

        # Update camera position and orientation
        camera_distance = 10  # Adjust this value to change the distance between the camera and the bus
        camera_height = 5  # Adjust this value to change the height of the camera

        # Calculate the camera position relative to the bus
        camera_pos = self.model4.getPos(self.model1) - (self.model4.getQuat(self.model1).getForward() * camera_distance)
        camera_pos.setZ(camera_pos.getZ() + camera_height)

        # Cast a ray from the camera's desired position downward to detect the ground
        self.pickerRay.setOrigin(camera_pos)
        self.pickerRay.setDirection(Vec3(0, 0, -1))  # Cast the ray downward
        self.picker.traverse(self.render)

        if self.pickerQueue.getNumEntries() > 0:
            self.pickerQueue.sortEntries()
            ground_point = self.pickerQueue.getEntry(0).getSurfacePoint(self.render)
            ground_height = ground_point.getZ()
            camera_pos.setZ(ground_height + camera_height)

        self.cam.setPos(camera_pos)
        self.cam.lookAt(self.model4)

        # Play engine sound when accelerating
        #if self.direction.getX() != 0 and not self.engine_sound.get_busy():
            #self.engine_sound.play(-1)  # Loop the engine sound infinitely
        # Stop engine sound when not accelerating
        #elif self.direction.getX() == 0 and self.engine_sound.get_busy():
            #self.engine_sound.stop()

        # Traverse the scene to detect and handle collisions
        self.collision_traverser.traverse(self.render)

        # Repeat the task every frame
        return Task.cont

    #accelerate using w key
    def accelerate(self):
        self.engine_sound.play()
        self.direction = Vec3(1, 0, 0)

    #reverse using s key
    def reverse(self):
        self.engine_sound.play()
        self.direction = Vec3(-1, 0, 0)

    #stop acceleration using w-up key
    def stop_acceleration(self):
        self.engine_sound.stop()
        self.direction = Vec3(0, 0, 0)

    #left turn using a key
    def turn_left(self):
        self.engine_sound.play()
        self.turn_speed = -1

    #right turn using d key
    def turn_right(self):
        self.engine_sound.play()
        self.turn_speed = 1

    #stop turnung using a-p and d-up
    def stop_turning(self):
        self.engine_sound.stop()
        self.turn_speed = 0

    #move left using q key
    def move_left(self):
        self.engine_sound.play()
        self.lateral_direction = Vec3(0, 0, -1)

    #move right using e key
    def move_right(self):
        self.engine_sound.play()
        self.lateral_direction = Vec3(0, 0, 1)

    #stop lateral movement using q-up and e-up
    def stop_lateral_movement(self):
        self.engine_sound.stop()
        self.lateral_direction = Vec3(0, 0, 0)

    #play horn using h key
    def play_horn(self):
        self.horn_sound.play()

    def music_system(self):
        if self.musicsystem_sound.status() == self.musicsystem_sound.PLAYING:
            self.musicsystem_sound.stop()
        else:
            self.musicsystem_sound.setLoop(True)
            self.musicsystem_sound.play()

    #background music using m key
    def toggle_background_music(self):
        if self.background_music.status() == self.background_music.PLAYING:
            self.background_music.stop()
        else:
            self.background_music.setloop(True)
            self.background_music.play()

    def music_system(self):
        if self.musicsystem_sound.status() == self.musicsystem_sound.PLAYING:
            self.musicsystem_sound.stop()
        else:
            self.musicsystem_sound.setLoop(True)
            self.musicsystem_sound.play()

game = Car()
game.run()