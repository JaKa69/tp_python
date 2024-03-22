let canvas;
let ctx;
let delay = 200;
let xCoord = 0;
let yCoord = 0;
let snakeSize = 20;
let appleX = 0;
let appleY = 0;
let xVelocity = 0;
let yVelocity = 0;
let score = 0;
let index = [];
let isGameOver = false;

document.addEventListener('DOMContentLoaded', function() {
    const startBtn = document.getElementById('start');
    startBtn.addEventListener('click', () => {
    init();
    });
});

document.addEventListener('keydown', (event) => {
    const keyCode = event.code;
    switch (keyCode) {
        case 'ArrowLeft':
            if (xVelocity === 0) {
                xVelocity = -snakeSize;
                yVelocity = 0;
            }
            break;
        case 'ArrowUp':
            if (yVelocity === 0) {
                xVelocity = 0;
                yVelocity = -snakeSize;
            }
            break;
        case 'ArrowRight':
            if (xVelocity === 0) {
                xVelocity = snakeSize;
                yVelocity = 0;
            }
            break;
        case 'ArrowDown':
            if (yVelocity === 0) {
                xVelocity = 0;
                yVelocity = snakeSize;
            }
            break;
    }
});


function init() {
    canvas = document.getElementById('canvas');
    ctx = canvas.getContext('2d');
    createApple();
    xVelocity = snakeSize;
    index = JSON.parse(localStorage.getItem('snake')) || [{x: canvas.width / 2, y: canvas.height / 2}];
    setInterval(game, delay);
}

function createApple() {
    appleX = Math.floor(Math.random() * (canvas.width / snakeSize)) * snakeSize;
    appleY = Math.floor(Math.random() * (canvas.height / snakeSize)) * snakeSize;
}

function paint() {
    ctx.fillStyle = 'white';
    ctx.fillRect(0, 0, canvas.width, canvas.height);

    ctx.strokeStyle = 'black';
    ctx.lineWidth = 1;

    for (let x = 0; x < canvas.width; x += snakeSize) {
        ctx.beginPath();
        ctx.moveTo(x, 0);
        ctx.lineTo(x, canvas.height);
        ctx.stroke();
    }

    for (let y = 0; y < canvas.height; y += snakeSize) {
        ctx.beginPath();
        ctx.moveTo(0, y);
        ctx.lineTo(canvas.width, y);
        ctx.stroke();
    }

    ctx.fillStyle = 'red';
    ctx.fillRect(appleX, appleY, snakeSize, snakeSize);

    ctx.fillStyle = 'green';
    for (let i = 0; i < index.length; i++) {
        ctx.fillRect(index[i].x, index[i].y, snakeSize, snakeSize);
    }
}

function move() {
    xCoord += xVelocity;
    yCoord += yVelocity;

    if (xCoord < 0 || xCoord >= canvas.width || yCoord < 0 || yCoord >= canvas.height) {
        gameOver();
        return;
    }

    for (let i = 0; i < index.length; i++) {
        if (xCoord === index[i].x && yCoord === index[i].y) {
            gameOver();
            return;
        }
    }

    if (xCoord === appleX && yCoord === appleY) {
        score++;
        createApple();
        index.push({x: xCoord, y: yCoord});
    } else {
        index.shift();
        index.push({x: xCoord, y: yCoord});
    }
}

function game() {
    move();
    paint();
    document.getElementById('score').innerText = `Score: ${score}`;
}

function gameOver() {
    if (isGameOver) return;
    isGameOver = true;
    clearInterval();
    // Envoie le score au serveur
    fetch('/add_score', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
        },
        body: `score=${score}`,
    })
    .then(response => response.text())
    .then(() => {
        alert(`Game Over! Your score is ${score}`);
        window.location.reload();
    })
    .catch((error) => {
        console.error('Error:', error);
    });
}


window.addEventListener('unload', () => {
    localStorage.setItem('index', JSON.stringify(index));
});
