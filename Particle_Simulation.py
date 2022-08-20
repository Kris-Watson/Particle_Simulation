from asyncio.windows_events import NULL
from ctypes.wintypes import PSIZE
from flask import Flask, render_template
import numpy as np
import time
import math
from numpy.random import default_rng as rng
import re
import configparser

app = Flask(__name__, template_folder='templates')

#==========================================================================#
#--------------- User changable data in Initial_params.txt ----------------#
#==========================================================================#

#----- Particle space definition
class IniParticles:
	#------------- Initialize variables
	def __init__(self, pos, vel, radius):
		self.particles = pos
		self.velocities = vel
		self.data=[pos]
		self.pSize = pos.shape
		self.vSize = vel.shape
		self.radius = radius
		if self.pSize != self.vSize:
			raise Exception("Unequal number of positions and velocities for particles")
	
		#----------- Checks if any particles are spawned in the same position and corrects it
		unq, cnt = np.unique(self.particles, axis=0, return_counts=True)	
		for i in cnt:
			if i > 1:
				raise Exception("Multiple particles in same initial position")
	
	#---------- Updates position
	def updatePositions(self):
		particleIndex = 0
		dimensionIndex = 1
		for i in range(0, self.pSize[particleIndex]):
			self.particles[i] = self.particles[i] + self.velocities[i] #new position based on velocity

			#------------- Boundary condition to bounce off walls
			for j in range(0, self.pSize[dimensionIndex]):
				if ((self.particles[i,j]<=-0.95)and(self.velocities[i,j]<0))or((self.particles[i,j]>=0.95)and(self.velocities[i,j]>0)):
					self.velocities[i,j] = -self.velocities[i,j]
	
			#----------- Check if current particle is close to any other particle
			closeParticleIndices = self.checkProximity(self.particles[i], i) # i is the current position index

			#----------- If particles are close, check for collision. If yes, calculate new velocity
			if (closeParticleIndices != []):
				self.checkCollision(i, closeParticleIndices)

		#------------ Update variable that will be sent to js to be drawn
		self.data=np.append(self.data,[self.particles],axis=0)

	#----------- Check if current particle is close to any other particle
	def checkProximity(self, tempPosition, currentParticleIndex):
		checkProximityRadius = np.array([0.1,0.1]) # Aribitrary proximity to check
		closeParticleIndices = []
		#-------------- Checks distance between the centers of particles
		for i in range(0, len(self.particles[:currentParticleIndex])):
			distanceXY = np.subtract(tempPosition,self.particles[i])
			if ((abs(distanceXY) < checkProximityRadius).all()):
				closeParticleIndices.append(i)

		return closeParticleIndices

	#-------------- Checks if collision occurs and updates velocity array
	def checkCollision(self, currentParticleIndex, closeParticleIndices):
		body1Pos = self.particles[currentParticleIndex]
		body1Vel = self.velocities[currentParticleIndex]
		mass = 1 # Placeholder
		x=0
		y=1
		for i in closeParticleIndices:
			body2Pos = self.particles[i]
			body2Vel = self.velocities[i]
			distanceVector = np.subtract(body1Pos,body2Pos)
			distance = np.linalg.norm(distanceVector)
			if (distance <= self.radius * 2):
				#------------ Constants
				if distanceVector[x] == 0:
					theta = math.pi/4
				else: 
					if distanceVector[y] == 0:
						theta = 0
					else:
						theta = math.atan(distanceVector[y] / distanceVector[x])
				cosTheta = math.cos(theta)
				sinTheta = math.sin(theta)
				"""# Test for momentum conservation
				initialMomentum = mass * np.linalg.norm([body1Vel[x]-body2Vel[x], body1Vel[y]-body2Vel[y]])"""
				
				#------------- Calculation for new velocity
					# Resolve velocities to new reference frame along impact normal (x hat direction)
					# Particles exchange velocities along impact normal
				body1finalVelXhat = body2Vel[x]*cosTheta + body2Vel[y]*sinTheta
				body2finalVelXhat = body1Vel[x]*cosTheta + body1Vel[y]*sinTheta
				
				body1finalVelYhat = body1Vel[x]*sinTheta - body1Vel[y]*cosTheta
				body2finalVelYhat = body2Vel[x]*sinTheta - body2Vel[y]*cosTheta

					# Resolve velocities to original reference frame
				body1finalVelocityX = body1finalVelXhat*cosTheta + body1finalVelYhat*sinTheta
				body1finalVelocityY = body1finalVelXhat*sinTheta - body1finalVelYhat*cosTheta

				body2finalVelocityX = body2finalVelXhat*cosTheta + body2finalVelYhat*sinTheta
				body2finalVelocityY = body2finalVelXhat*sinTheta - body2finalVelYhat*cosTheta

				self.velocities[currentParticleIndex] = [body1finalVelocityX, body1finalVelocityY]
				self.velocities[i] = [body2finalVelocityX, body2finalVelocityY]

				"""#--------------- Test to ensure math is correct			
				finalMomentum = mass * np.linalg.norm([body1finalVelocityX-body2finalVelocityX, body1finalVelocityY-body2finalVelocityY])
				if (finalMomentum - initialMomentum > 0.00000001):
					print("Lost Momentum")"""


def readIniFile():
	config = configparser.ConfigParser()
	config.read('Initial_Params.ini')
	pNumber = 	int(config['Particle']['Number'])
	pVelocity = 	float(config['Particle']['Velocity'])
	pRadius = 	float(config['Particle']['Number'])
	sSize = 	config['Simulation']['Size']
	sDuration = 	int(config['Simulation']['Duration'])

	return {"pNumber": pNumber, "pVelocity": pVelocity, "pRadius": pRadius, "sSize": sSize, "sDuration": sDuration}



def main():
	fileData = readIniFile()
	#==========================================================================#
	#------ Initialize Data. CHANGE THESE VARIABLES TO ADJUST GENERATION ------#
	#==========================================================================#
	numberOfParticles	=	1 * 	fileData.get('pNumber')		# Number of particles generated by random generator
	velocityMultiplier	=	0.01 * 	fileData.get('pVelocity')		# Multiply all velocities by this value
	radiusOfparticles	=	0.01 * 	fileData.get('pRadius')	# Hitbox for collisions (Currently doesn't update visually in webgl)
	worldSize		=	1 * 	fileData.get('sSize')		# Worldsize - larger world means more space for particles to move (Does not change size of canvas in webgl)
	simDuration		=	1 * 	fileData.get('sDuration')	# Duration of simulation in ms
	

	#----------- Functions to spawn particles using user data
	particlePositions = np.random.randint(0, 100, size=(numberOfParticles, 2)).argsort(axis = 0).astype(float) # Creates random particle positions
	particleVelocities = np.random.rand(numberOfParticles, 2)# Asigns velocity to above particles

	#----------- Normalize data for webgl
	normalizedParticlePositions = np.subtract(np.divide(particlePositions, (np.amax(particlePositions)/ 2.0)), 1.0 )
	normalizedParticleVelocities =  np.multiply(np.subtract(particleVelocities, 0.5), velocityMultiplier)

	print(normalizedParticlePositions)
	#----------- Initialize space
	space = IniParticles(normalizedParticlePositions, normalizedParticleVelocities, radiusOfparticles)

	#----------- Loop to update particle positions
	print("Generating data:") 
	for i in range(0,simDuration):
		space.updatePositions()
		if (i % (simDuration / 4) == 0):
			print(int(i/simDuration * 100), "%")
	print("Done! Starting flask server...")
	time.sleep(1)
	return space.data


if __name__ == "__main__":
	#------------ Convert data to list for js
	sendToJSTemplate = main().tolist()

	#------------ Flask sends data to html as variable "data"
	@app.route('/')
	def index(indexData=sendToJSTemplate):
		return render_template('index.html', data=indexData)
	app.run()
