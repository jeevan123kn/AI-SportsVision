export const SPORT_ACTIVITIES = {
  Cricket: ['Batting', 'Bowling', 'Fielding', 'Wicketkeeping'],
  Football: ['Shooting', 'Passing', 'Dribbling', 'Defending', 'Goalkeeping'],
  Basketball: ['Shooting', 'Dribbling', 'Passing', 'Defense', 'Rebounding'],
  Tennis: ['Serve', 'Forehand', 'Backhand', 'Volley', 'Footwork'],
  Badminton: ['Serve', 'Smash', 'Drop Shot', 'Clear', 'Net Play', 'Footwork'],
  Volleyball: ['Serving', 'Spiking', 'Blocking', 'Setting', 'Digging'],
  Hockey: ['Dribbling', 'Passing', 'Shooting', 'Defending', 'Goalkeeping'],
  'Table Tennis': ['Serve', 'Forehand', 'Backhand', 'Smash', 'Footwork'],
  Athletics: ['Sprinting', 'Distance Running', 'Hurdles', 'Long Jump', 'High Jump', 'Throwing'],
  Swimming: ['Freestyle', 'Backstroke', 'Breaststroke', 'Butterfly', 'Individual Medley'],
};

export const getValidActivity = (sport, activity) => {
  const activities = SPORT_ACTIVITIES[sport] || [];
  return activities.find((item) => item.toLowerCase() === activity?.toLowerCase()) || '';
};