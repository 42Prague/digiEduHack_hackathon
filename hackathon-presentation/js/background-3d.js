// Space background: layered starfield + your rotating torus knot in the center

// Guard in case THREE is not loaded or canvas missing
if (window.THREE) {
  const canvas = document.getElementById("bg-canvas");
  if (canvas) {
    const renderer = new THREE.WebGLRenderer({
      canvas,
      antialias: true,
      alpha: true,
    });

    const scene = new THREE.Scene();
    const camera = new THREE.PerspectiveCamera(
      45,
      window.innerWidth / window.innerHeight,
      0.1,
      400
    );
    camera.position.z = 6;

    // -----------------------------
    // CENTRAL OBJECT: TORUS KNOT
    // -----------------------------
    const geometry = new THREE.TorusKnotGeometry(1.4, 0.4, 128, 32);
    const material = new THREE.MeshStandardMaterial({
      color: 0x60a5fa,
      metalness: 0.4,
      roughness: 0.25,
      emissive: 0x111827,
      emissiveIntensity: 0.7,
    });

    const mesh = new THREE.Mesh(geometry, material);
    scene.add(mesh);

    // Lights for torus + stars
    const backLight = new THREE.PointLight(0xec4899, 1.5, 40);
    backLight.position.set(-4, -2, -6);
    scene.add(backLight);

    const keyLight = new THREE.PointLight(0x93c5fd, 1.6, 40);
    keyLight.position.set(4, 3, 6);
    scene.add(keyLight);

    const ambient = new THREE.AmbientLight(0x111827, 0.9);
    scene.add(ambient);

    // -----------------------------
    // STARFIELD (3 layers)
    // -----------------------------
    function createStarLayer(options) {
      const {
        count,
        spread,
        size,
        opacity,
        color,
        twinkleAmount = 0,
        twinkleSpeed = 1,
      } = options;

      const geometry = new THREE.BufferGeometry();
      const positions = new Float32Array(count * 3);
      const phases = new Float32Array(count); // for twinkling variation

      for (let i = 0; i < count; i++) {
        const i3 = i * 3;
        positions[i3 + 0] = (Math.random() - 0.5) * spread; // x
        positions[i3 + 1] = (Math.random() - 0.5) * spread; // y
        positions[i3 + 2] = (Math.random() - 0.5) * spread; // z
        phases[i] = Math.random() * Math.PI * 2;
      }

      geometry.setAttribute("position", new THREE.BufferAttribute(positions, 3));
      geometry.setAttribute("phase", new THREE.BufferAttribute(phases, 1));

      const material = new THREE.PointsMaterial({
        color,
        size,
        transparent: true,
        opacity,
        sizeAttenuation: true,
        depthWrite: false,
      });

      const points = new THREE.Points(geometry, material);
      points.userData = {
        twinkleAmount,
        twinkleSpeed,
      };

      return points;
    }

    // Far background: tiny, dim stars
    const starsFar = createStarLayer({
      count: 2000,
      spread: 300,
      size: 0.05,
      opacity: 0.5,
      color: 0xffffff,
      twinkleAmount: 0.1,
      twinkleSpeed: 0.4,
    });
    scene.add(starsFar);

    // Mid layer: medium stars
    const starsMid = createStarLayer({
      count: 1200,
      spread: 200,
      size: 0.09,
      opacity: 0.8,
      color: 0xe5e7eb,
      twinkleAmount: 0.25,
      twinkleSpeed: 0.7,
    });
    scene.add(starsMid);

    // Near layer: bright “foreground” stars
    const starsNear = createStarLayer({
      count: 600,
      spread: 120,
      size: 0.16,
      opacity: 1,
      color: 0xf9fafb,
      twinkleAmount: 0.4,
      twinkleSpeed: 1.2,
    });
    scene.add(starsNear);

    const starLayers = [starsFar, starsMid, starsNear];

    // -----------------------------
    // RESIZE
    // -----------------------------
    function resizeRenderer() {
      const width = window.innerWidth;
      const height = window.innerHeight;
      renderer.setSize(width, height, false);
      camera.aspect = width / height;
      camera.updateProjectionMatrix();
    }

    resizeRenderer();
    window.addEventListener("resize", resizeRenderer);

    // -----------------------------
    // ANIMATION
    // -----------------------------
    let lastTime = 0;

    function animate(time) {
      const dt = (time - lastTime) / 1000 || 0.016;
      lastTime = time;

      // Rotate the central shape
      mesh.rotation.y += dt * 0.35;
      mesh.rotation.x += dt * 0.15;

      // Slow rotation of star layers for parallax / dimension
      starsFar.rotation.y += dt * 0.003;
      starsMid.rotation.y += dt * 0.006;
      starsNear.rotation.y += dt * 0.01;

      // Twinkle effect
      starLayers.forEach((points) => {
        const { twinkleAmount, twinkleSpeed } = points.userData;
        if (!twinkleAmount) return;

        const geom = points.geometry;
        const phases = geom.getAttribute("phase");
        const baseOpacity = points.material.opacity;

        // Apply a global twinkle wave, modulated per-star by its phase
        const t = time * 0.001 * twinkleSpeed;
        const count = phases.count;

        // We don't change individual opacities per-star (would require per-vertex colors),
        // but we modulate the whole layer subtly to give a breathing effect,
        // while the different phases make motion feel less uniform.
        const wave =
          1.0 + Math.sin(t + phases.getX(0)) * (twinkleAmount * 0.6);

        points.material.opacity = baseOpacity * wave;
      });

      renderer.render(scene, camera);
      requestAnimationFrame(animate);
    }

    requestAnimationFrame(animate);
  }
}
