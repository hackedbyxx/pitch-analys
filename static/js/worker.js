// worker.js
var count = 0;
var runTime;
var startTime = performance.now();

onmessage = function(e) {   // 从主文件传值过来会触发onmessage事件，接收参数
   let x = e.data.x;
   let graph = e.data.graph;
   interval = setInterval(function () {
      if (pitches[x]) {
         Plotly.relayout(graph, {
            shapes: [{
               type: "line",
               line: {
                  color: "red",
               },
               fillcolor: 'red',
               x0: x * 0.01,
               x1: x * 0.01,
               // ysizemode: 'pixel', //Default: "scaled"
               y0: 0,
               y1: 1,
               yref: 'paper'
            }]
         });
      }// console.log(pitches[x]-50, pitches[x]+50)
      if (data.notes[x]) {
         Plotly.update("plot", {}, getAnnotations(data.notes[x]));
      }
      x += 10;

   }, 100);
   this.postMessage(interval);
}


