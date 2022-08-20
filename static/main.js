var InitDemo = function () {
	// Collected python data is in JSON format. Converts to a 3D array
	var jsData = JSON.parse(newData);
	var particleNumber = jsData[0].length
	var particleDimensions = jsData[0][0].length

    /*================Creating a canvas=================*/
	var canvas = document.getElementById('game-surface');
	var gl = canvas.getContext('webgl');

	if (!gl) {
		console.log('WebGL not supported, falling back on experimental gl');
		gl = canvas.getContext('experimental-gl');
	}

	if (!gl) {alert('Your browser doesnt support webgl');}


    // Create an empty buffer object to store the vertex buffer
	var vertex_buffer = gl.createBuffer();

	//Bind appropriate array buffer to it
    gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
    // Pass the vertex data to the buffer
    gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(jsData[0].flat()), gl.DYNAMIC_DRAW);
    // Unbind the buffer
    gl.bindBuffer(gl.ARRAY_BUFFER, null);



   	/*=========================Shaders========================*/

	// vertex shader source code
	var vertCode =
		'attribute vec3 coordinates;' +
	  	'void main(void) {' +
		'gl_Position = vec4(coordinates, 1.0);' +
		'gl_PointSize = 10.0;'+
		'}';

	// Create a vertex shader object
	var vertShader = gl.createShader(gl.VERTEX_SHADER);	   
	// Attach vertex shader source code
	gl.shaderSource(vertShader, vertCode);
	// Compile the vertex shader
	gl.compileShader(vertShader);

	// fragment shader source code
	var fragCode =
		'void main(void) {' +
		' gl_FragColor = vec4(0.0, 0.0, 0.0, 0.1);' +
		'}';

	// Create fragment shader object
	var fragShader = gl.createShader(gl.FRAGMENT_SHADER);
	// Attach fragment shader source code
	gl.shaderSource(fragShader, fragCode);
	// Compile the fragment shader
	gl.compileShader(fragShader);
	   
	// Create a shader program object to store the combined shader program
	var shaderProgram = gl.createProgram();
	// Attach a vertex shader
	gl.attachShader(shaderProgram, vertShader); 
	// Attach a fragment shader
	gl.attachShader(shaderProgram, fragShader);
	// Link both programs
	gl.linkProgram(shaderProgram);
	// Use the combined shader program object
	gl.useProgram(shaderProgram);



	/*======== Associating shaders to buffer objects ========*/

	// Bind vertex buffer object
	gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);

	// Get the attribute location
	var coord = gl.getAttribLocation(shaderProgram, "coordinates");

	// Point an attribute to the currently bound VBO
	gl.vertexAttribPointer(coord, particleDimensions, gl.FLOAT, gl.FALSE, particleDimensions * Float32Array.BYTES_PER_ELEMENT, 0);
	// Enable the attribute
	gl.enableVertexAttribArray(coord);

	/*============= Drawing the primitive ===============*/

    // Clear the canvas
    gl.clearColor(0.5, 0.5, 0.5, 0.9);
    // Enable the depth test
    gl.enable(gl.DEPTH_TEST);
    // Clear the color buffer bit
    gl.clear(gl.COLOR_BUFFER_BIT);
    // Set the view port
    gl.viewport(0,0,canvas.width,canvas.height);


	/*=========== Loop to draw moving particles ================*/

	// Initialise counters
	var counter = 0
	var i = 0
	
	var loop = function (){
		// Every x/60s draw new particle
		// Updates buffer data
		gl.bindBuffer(gl.ARRAY_BUFFER, vertex_buffer);
		gl.bufferData(gl.ARRAY_BUFFER, new Float32Array(jsData[i].flat()), gl.DYNAMIC_DRAW);

		// Clears old particles
		gl.clearColor(0.5, 0.5, 0.5, 0.9);
		gl.clear(gl.COLOR_BUFFER_BIT);

		// Draws new particles
		gl.drawArrays(gl.POINTS, 0, particleNumber);
		i++;
		if (i < jsData.length) {requestAnimationFrame(loop);}
	}
	// Calls loop every 1/60 s
	requestAnimationFrame(loop); 
}