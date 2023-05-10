set terminal pngcairo transparent enhanced font "arial,10" fontscale 1.0 size {width}, {height}
set output '{tmp_chart_file}'
set key autotitle columnhead

#set multiplot
#set size 1, 0.5

#set tics in
#unset tics
#set tic scale 0

# Display border
set border lt 4
# unset border

# Set fixed ticks
set xtics 20

# Set y axis to start at 0
set yrange [0:*]

# Set x axis to start at frame number
set xrange [{frame_start_number}:*]

#set origin 0.0,0.5
# unset xtics
# set y2label "speed" textcolor lt 4
set key textcolor variable
#plot '{frames_stats_file}' using 1:3 with lines lt 4 title 'Memory (MB)'

#set origin 0.0,0.0
plot '{frames_stats_file}' using 1:4 with lines lt 4 title 'Render time (m)'

#unset multiplot

