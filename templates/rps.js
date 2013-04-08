rps = {}

/* Test data
rps.chain = [[.2,.2,.6],
             [.4,.6,.0], [.1,.7,.2], [.5,.3,.2]]*/
rps.chain = {{ chain }}

// Compute the depth of the chain (how many moves we are digesting)
rps.chain_depth = Math.floor(Math.log(rps.chain.length) / Math.log(3))
rps.score = 0
rps.key = ["Rock", "Paper", "Scissors"]
rps.victory_key = ["lose", "tie", "win"]
rps.history = []
rps.history_el = null
rps.report_el = null
rps.baseurl = "{{ baseurl }}"

/**
 * Return 0 for tie, 1 if a win, -1 if a loss
 */
rps.victor = function(a,b) {
    // MUST ADD 4 since modulo isn't properly
    // implemented for negative numbers in js
    return (((4 + a - b) % 3) - 1)
}
_.map([["Rock", "Rock", 0],
       ["Rock", "Paper", -1],
       ["Rock", "Scissors", 1],

       ["Paper", "Paper", 0],
       ["Paper", "Scissors", -1],
       ["Paper", "Rock", 1],

       ["Scissors", "Rock", -1],
       ["Scissors", "Paper", 1],
       ["Scissors", "Scissors", 0]], function(t) {
    // Test all the possible inputs
    var ret = rps.victor(rps.key.indexOf(t[0]),rps.key.indexOf(t[1]))
    if (ret != t[2]) {
        console.error("Test case " + t[0] + " vs " + t[1] + " returned " +
                      ret + " but should have returned " + t[2])
    }
})

/**
 * Given the last [depth] positions in the history move list, compute the next
 * array position in the markov chain
 */
rps.get_next_move = function() {
    var moves = rps.history.slice(-rps.chain_depth)
    var compute_chain_position_ = function(pos, moves) {
        if (moves.length == 0) {
            return pos
        }

        return compute_chain_position_(pos * 3 + moves[0], moves.slice(1))
    }

    var move_probabilities = rps.chain[compute_chain_position_(0, moves)]

    if (move_probabilities == -1) {
        // We have hit an unexplored branch in our RPS tree, pick at random
        return Math.floor(Math.random() * 3)
    }

    // move_probabilities is a triplet of the probability to select RP and S
    var move = -1; // Start with rock
    var move_selection = Math.random()
    do {
        move_selection -= move_probabilities[0]

        // Chop off the next probability
        move_probabilities = move_probabilities.slice(1)

        // Now count the actual move we are on
        move++
    } while (move_probabilities.length && move_selection > 0)

    // Now we have our guess at what the user will pick.
    // So now, Rock => Paper => Scissors => Rock
    return (move + 1) % 3;
}

/**
 * Function to generate other move functions
 */
rps.move_ = function(player) {
    return function() {
        // Get the computers play FIRST so that we can't cheat
        var comp = rps.get_next_move();

        // Score and tally the play
        var victor = rps.victor(player, comp)
        rps.score += victor

        // Record the users play and report it to the server
        rps.history.push(player)
        rps.history_el.attr('src', rps.baseurl
                                + "/feedback.gif?h=" + rps.history.join("")
                                + "&cache=" + Math.floor(Math.random() * 99999))

        report = "Computer plays " + rps.key[comp] +
                 " against your " + rps.key[player] +
                 ". You " + rps.victory_key[victor + 1] +
                 "! Your score is now: " + rps.score
        console.log(report)
        rps.report_el.text(report)
    }
}

rps.rock     = rps.move_(0)
rps.paper    = rps.move_(1)
rps.scissors = rps.move_(2)

/**
 * Start parsing
 */
rps.main = function(body) {
    $(body).html("<div id='report'></div><button id='rock'>Rock</button><button id='paper'>Paper</button><button id='scissors'>Scissors</button><img class='hide' id='feedback' />")

    $('#rock').click(rps.rock)
    $('#paper').click(rps.paper)
    $('#scissors').click(rps.scissors)
    rps.history_el = $('#feedback')
    rps.report_el = $('#report')
}

/**
 * RPS markov chain
 */
/*
      0
    / |   \
  1   2      3
 /|\ /|\   / | \
 456 789 10 11 12

r: n*3 + 1
p: n*3 + 2
s: n*3 + 3

0*3 + 1 = 1 r
0*3 + 2 = 2 p
0*3 + 3 = 3 s

1*3 + 1 = 4 r
1*3 + 2 = 5 p
1*3 + 3 = 6 s

2*3 + 1 = 7 r
2*3 + 2 = 8 p
2*3 + 3 = 9 s

3*3 + 1 = 10 r
3*3 + 2 = 11 p
3*3 + 3 = 12 s
*/