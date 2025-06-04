program ComplexExample;
var
  counter: integer;
  total: integer;
  isPositive: boolean;
begin
  counter := 10;
  total := 5 + 3; 
  isPositive := counter > 0;
  while counter > 0 do
  begin
    total := total + counter;
    counter := counter - 1;
  end;
  if isPositive then
  begin
    writeln('Total is: ', total);
  end
  else
  begin
    writeln('Counter was not positive');
  end
end.
