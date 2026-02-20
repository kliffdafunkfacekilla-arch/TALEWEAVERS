import { Filter } from 'pixi.js';

// Simple ambient + point light shader
// Uses screen coordinates to calculate distance to lights
const fragmentShader = `
precision mediump float;

in vec2 vTextureCoord;
out vec4 finalColor;

uniform sampler2D uTexture;
uniform vec2 uLightPos;
uniform vec3 uLightColor;
uniform float uLightRadius;
uniform float uAmbientLight;
uniform vec2 uDimensions;

void main(void) {
    // Current pixel color from the map texture
    vec4 texColor = texture(uTexture, vTextureCoord);
    
    // Pixel coordinate on screen
    vec2 pixelPos = vTextureCoord * uDimensions;
    
    // Distance to light
    float dist = distance(pixelPos, uLightPos);
    
    // Attenuation (falloff)
    float attenuation = clamp(1.0 - (dist / uLightRadius), 0.0, 1.0);
    // Smooth falloff
    attenuation = attenuation * attenuation; 
    
    // Calculate final light intensity
    vec3 ambient = vec3(uAmbientLight);
    vec3 light = uLightColor * attenuation;
    
    // Combine lighting
    vec3 finalLight = ambient + light;
    
    // Apply to texture color
    finalColor = vec4(texColor.rgb * finalLight, texColor.a);
}
`;

export class DynamicLightFilter extends Filter {
    constructor(
        width: number,
        height: number,
        lightPos: { x: number, y: number } = { x: 0, y: 0 },
        radius: number = 300
    ) {
        super({
            glProgram: {
                fragment: fragmentShader
            },
            resources: {
                localUniforms: {
                    uLightPos: { value: [lightPos.x, lightPos.y], type: 'vec2<f32>' },
                    uLightColor: { value: [1.0, 0.9, 0.6], type: 'vec3<f32>' }, // Warm torch light
                    uLightRadius: { value: radius, type: 'f32' },
                    uAmbientLight: { value: 0.2, type: 'f32' }, // Dark ambient
                    uDimensions: { value: [width, height], type: 'vec2<f32>' }
                }
            }
        });
    }

    updateLight(x: number, y: number, radius: number) {
        this.resources.localUniforms.uniforms.uLightPos = [x, y];
        this.resources.localUniforms.uniforms.uLightRadius = radius;
    }

    updateDimensions(width: number, height: number) {
        this.resources.localUniforms.uniforms.uDimensions = [width, height];
    }
}
