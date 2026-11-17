// Original example. The output wraps modulo 256.
module execution_slice(
    input wire clk, reset, enable,
    input wire a, b,
    input wire [7:0] x, y, z,
    output reg [7:0] q
);
    wire select_y = a & b;
    wire [7:0] selected = select_y ? y : z;
    always @(posedge clk) begin
        if (reset)
            q <= 8'b0;
        else if (enable)
            q <= x + selected;
    end
endmodule

module selection_miter(
    input wire a, b,
    input wire [7:0] x, y, z,
    output wire [7:0] reference_value, reversed_value,
    output wire equivalent_rewrite_diff, reversed_diff
);
    wire select_y = a & b;
    wire [7:0] sum_y = x + y;
    wire [7:0] sum_z = x + z;
    wire [7:0] rewritten = select_y ? sum_y : sum_z;
    assign reference_value = x + (select_y ? y : z);
    assign reversed_value = select_y ? sum_z : sum_y;
    assign equivalent_rewrite_diff = (reference_value != rewritten);
    assign reversed_diff = (reference_value != reversed_value);
endmodule
