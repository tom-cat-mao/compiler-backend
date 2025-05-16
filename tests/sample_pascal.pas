program SamplePascal;
var
  x, y, z: integer;
  condition: boolean;
begin
  x := 10;
  y := 20;
  z := x + y * 2;
  condition := (x < y) and (y > 0);
  
  if condition then
    begin
      z := z - 5;
      writeln('Condition is true, z is now: ', z);
    end
  else
    begin
      z := z + 5;
      writeln('Condition is false, z is now: ', z);
    end;
  
  while x < 15 do
    begin
      x := x + 1;
      writeln('Incrementing x to: ', x);
    end;
  
  writeln('Final values: x=', x, ', y=', y, ', z=', z);
end.
