#version 140

// The builtin sprite program; pixels outside clip.x..clip.y (world x) are dropped: a Kong
// walking through a door is hidden by the door frame, as the original's BG1 priority does.
in mediump vec2 var_texcoord0;
in highp float var_x;

out vec4 out_fragColor;

uniform mediump sampler2D texture_sampler;
uniform fs_uniforms
{
    mediump vec4 tint;
    highp vec4 clip;
};

void main()
{
    if (var_x < clip.x || var_x > clip.y) discard;
    // Pre-multiply alpha since all runtime textures already are
    mediump vec4 tint_pm = vec4(tint.xyz * tint.w, tint.w);
    out_fragColor = texture(texture_sampler, var_texcoord0.xy) * tint_pm;
}
