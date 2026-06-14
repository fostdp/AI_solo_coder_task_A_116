class SpinningWheel {
    constructor(scene) {
        this.scene = scene;
        this.group = new THREE.Group();
        this.spindles = [];
        this.yarns = [];
        this.wheelGroup = null;
        this.mainShaft = null;
        this.showYarn = true;
        this.wheelRotation = 0;
        this.spindleRotation = 0;
        this.time = 0;

        this.createFrame();
        this.createWaterWheel();
        this.createMainShaft();
        this.createSpindles();
        this.createYarns();

        this.scene.add(this.group);
    }

    createFrame() {
        const frameGroup = new THREE.Group();
        frameGroup.userData = {
            type: 'frame',
            name: '机架',
            description: '水转大纺车的木质机架，采用榫卯结构，支撑整个纺车系统。',
            material: '硬木（楠木、枣木）',
            height: '约2.5米',
            weight: '约500公斤'
        };

        const woodMaterial = new THREE.MeshStandardMaterial({
            color: 0x8B4513,
            roughness: 0.8,
            metalness: 0.2
        });

        const darkWoodMaterial = new THREE.MeshStandardMaterial({
            color: 0x654321,
            roughness: 0.85,
            metalness: 0.15
        });

        const legGeometry = new THREE.BoxGeometry(0.3, 5, 0.3);
        const legPositions = [
            { x: -4, z: -2 },
            { x: 4, z: -2 },
            { x: -4, z: 2 },
            { x: 4, z: 2 }
        ];

        legPositions.forEach(pos => {
            const leg = new THREE.Mesh(legGeometry, darkWoodMaterial);
            leg.position.set(pos.x, 2.5, pos.z);
            leg.castShadow = true;
            leg.receiveShadow = true;
            frameGroup.add(leg);
        });

        const beamGeometry1 = new THREE.BoxGeometry(8.6, 0.3, 0.3);
        const topBeam1 = new THREE.Mesh(beamGeometry1, woodMaterial);
        topBeam1.position.set(0, 5, -2);
        topBeam1.castShadow = true;
        frameGroup.add(topBeam1);

        const topBeam2 = new THREE.Mesh(beamGeometry1, woodMaterial);
        topBeam2.position.set(0, 5, 2);
        topBeam2.castShadow = true;
        frameGroup.add(topBeam2);

        const beamGeometry2 = new THREE.BoxGeometry(0.3, 0.3, 4.6);
        const sideBeam1 = new THREE.Mesh(beamGeometry2, woodMaterial);
        sideBeam1.position.set(-4, 5, 0);
        sideBeam1.castShadow = true;
        frameGroup.add(sideBeam1);

        const sideBeam2 = new THREE.Mesh(beamGeometry2, woodMaterial);
        sideBeam2.position.set(4, 5, 0);
        sideBeam2.castShadow = true;
        frameGroup.add(sideBeam2);

        const midBeamGeometry = new THREE.BoxGeometry(8.6, 0.2, 0.2);
        const midBeam1 = new THREE.Mesh(midBeamGeometry, darkWoodMaterial);
        midBeam1.position.set(0, 2.5, -2);
        midBeam1.castShadow = true;
        frameGroup.add(midBeam1);

        const midBeam2 = new THREE.Mesh(midBeamGeometry, darkWoodMaterial);
        midBeam2.position.set(0, 2.5, 2);
        midBeam2.castShadow = true;
        frameGroup.add(midBeam2);

        const diagonalGeometry = new THREE.CylinderGeometry(0.08, 0.08, 3.5, 8);
        const diagonal1 = new THREE.Mesh(diagonalGeometry, darkWoodMaterial);
        diagonal1.position.set(-2, 3.7, -2);
        diagonal1.rotation.z = Math.PI / 6;
        diagonal1.castShadow = true;
        frameGroup.add(diagonal1);

        const diagonal2 = new THREE.Mesh(diagonalGeometry, darkWoodMaterial);
        diagonal2.position.set(2, 3.7, -2);
        diagonal2.rotation.z = -Math.PI / 6;
        diagonal2.castShadow = true;
        frameGroup.add(diagonal2);

        this.frameGroup = frameGroup;
        this.group.add(frameGroup);
    }

    createWaterWheel() {
        this.wheelGroup = new THREE.Group();
        this.wheelGroup.userData = {
            type: 'waterWheel',
            name: '水轮',
            description: '水转大纺车的动力来源，水流冲击叶片带动水轮旋转，通过传动装置驱动锭子转动。',
            diameter: '约3米',
            bladeCount: '24片',
            material: '木质框架 + 竹制叶片',
            transmission: '齿轮传动'
        };

        const woodMaterial = new THREE.MeshStandardMaterial({
            color: 0x8B4513,
            roughness: 0.75,
            metalness: 0.1
        });

        const bambooMaterial = new THREE.MeshStandardMaterial({
            color: 0xDAA520,
            roughness: 0.6,
            metalness: 0.1
        });

        const hubGeometry = new THREE.CylinderGeometry(0.4, 0.4, 1.5, 16);
        const hub = new THREE.Mesh(hubGeometry, woodMaterial);
        hub.rotation.z = Math.PI / 2;
        hub.castShadow = true;
        this.wheelGroup.add(hub);

        const wheelRadius = 3;
        const rimGeometry = new THREE.TorusGeometry(wheelRadius, 0.15, 8, 32);
        const rim = new THREE.Mesh(rimGeometry, woodMaterial);
        rim.rotation.y = Math.PI / 2;
        rim.castShadow = true;
        this.wheelGroup.add(rim);

        const rim2 = new THREE.Mesh(rimGeometry, woodMaterial);
        rim2.rotation.y = Math.PI / 2;
        rim2.position.z = 1.2;
        rim2.castShadow = true;
        this.wheelGroup.add(rim2);

        const spokeCount = 12;
        const spokeGeometry = new THREE.BoxGeometry(0.1, wheelRadius - 0.4, 0.1);
        
        for (let i = 0; i < spokeCount; i++) {
            const angle = (i / spokeCount) * Math.PI * 2;
            
            const spoke1 = new THREE.Mesh(spokeGeometry, woodMaterial);
            spoke1.position.y = (wheelRadius - 0.4) / 2;
            spoke1.position.z = -0.6;
            spoke1.rotation.z = -angle;
            spoke1.castShadow = true;
            this.wheelGroup.add(spoke1);

            const spoke2 = new THREE.Mesh(spokeGeometry, woodMaterial);
            spoke2.position.y = (wheelRadius - 0.4) / 2;
            spoke2.position.z = 0.6;
            spoke2.rotation.z = -angle;
            spoke2.castShadow = true;
            this.wheelGroup.add(spoke2);
        }

        const bladeCount = 24;
        const bladeWidth = 0.6;
        const bladeHeight = 0.8;
        
        for (let i = 0; i < bladeCount; i++) {
            const angle = (i / bladeCount) * Math.PI * 2;
            const bladeGeometry = new THREE.BoxGeometry(bladeWidth, bladeHeight, 0.08);
            const blade = new THREE.Mesh(bladeGeometry, bambooMaterial);
            
            blade.position.x = Math.cos(angle) * wheelRadius;
            blade.position.y = Math.sin(angle) * wheelRadius;
            blade.rotation.z = angle + Math.PI / 2;
            blade.castShadow = true;
            
            this.wheelGroup.add(blade);
        }

        const gearGeometry = new THREE.CylinderGeometry(0.8, 0.8, 0.3, 32);
        const gear = new THREE.Mesh(gearGeometry, woodMaterial);
        gear.position.z = 1.2;
        gear.castShadow = true;
        this.wheelGroup.add(gear);

        for (let i = 0; i < 16; i++) {
            const angle = (i / 16) * Math.PI * 2;
            const toothGeometry = new THREE.BoxGeometry(0.15, 0.2, 0.3);
            const tooth = new THREE.Mesh(toothGeometry, woodMaterial);
            tooth.position.x = Math.cos(angle) * 0.85;
            tooth.position.y = Math.sin(angle) * 0.85;
            tooth.position.z = 1.2;
            tooth.rotation.z = angle;
            tooth.castShadow = true;
            this.wheelGroup.add(tooth);
        }

        this.wheelGroup.position.set(-8, 4, 0);
        this.group.add(this.wheelGroup);
    }

    createMainShaft() {
        const shaftGroup = new THREE.Group();
        shaftGroup.userData = {
            type: 'mainShaft',
            name: '主轴',
            description: '连接水轮和锭子的传动主轴，将水轮的旋转动力传递给32个锭子。',
            length: '约8米',
            diameter: '约20厘米',
            material: '硬木 + 铁轴套',
            transmissionRatio: '1:3.5'
        };

        const woodMaterial = new THREE.MeshStandardMaterial({
            color: 0x654321,
            roughness: 0.7,
            metalness: 0.2
        });

        const ironMaterial = new THREE.MeshStandardMaterial({
            color: 0x696969,
            roughness: 0.4,
            metalness: 0.8
        });

        const shaftGeometry = new THREE.CylinderGeometry(0.12, 0.12, 10, 16);
        const shaft = new THREE.Mesh(shaftGeometry, woodMaterial);
        shaft.rotation.z = Math.PI / 2;
        shaft.castShadow = true;
        shaftGroup.add(shaft);

        const ringGeometry = new THREE.TorusGeometry(0.15, 0.03, 8, 16);
        for (let i = 0; i < 8; i++) {
            const ring = new THREE.Mesh(ringGeometry, ironMaterial);
            ring.rotation.y = Math.PI / 2;
            ring.position.x = -4 + i * 1.2;
            ring.castShadow = true;
            shaftGroup.add(ring);
        }

        const driveGearGeometry = new THREE.CylinderGeometry(0.6, 0.6, 0.25, 32);
        const driveGear = new THREE.Mesh(driveGearGeometry, woodMaterial);
        driveGear.position.x = -5;
        driveGear.rotation.x = Math.PI / 2;
        driveGear.castShadow = true;
        shaftGroup.add(driveGear);

        for (let i = 0; i < 12; i++) {
            const angle = (i / 12) * Math.PI * 2;
            const toothGeometry = new THREE.BoxGeometry(0.12, 0.15, 0.25);
            const tooth = new THREE.Mesh(toothGeometry, woodMaterial);
            tooth.position.x = -5;
            tooth.position.y = Math.cos(angle) * 0.65;
            tooth.position.z = Math.sin(angle) * 0.65;
            tooth.rotation.y = angle;
            tooth.castShadow = true;
            shaftGroup.add(tooth);
        }

        this.mainShaft = shaftGroup;
        this.mainShaft.position.set(0, 4.8, 0);
        this.group.add(this.mainShaft);
    }

    createSpindles() {
        const spindleCount = 32;
        const rows = 2;
        const cols = 16;
        const spacing = 0.9;

        const spindleMaterial = new THREE.MeshStandardMaterial({
            color: 0xDAA520,
            roughness: 0.6,
            metalness: 0.2
        });

        const baseMaterial = new THREE.MeshStandardMaterial({
            color: 0x8B4513,
            roughness: 0.8,
            metalness: 0.1
        });

        this.spindleGroup = new THREE.Group();

        for (let row = 0; row < rows; row++) {
            for (let col = 0; col < cols; col++) {
                const spindleIndex = row * cols + col;
                const spindle = this.createSingleSpindle(spindleMaterial, baseMaterial, spindleIndex);
                
                const x = -((cols - 1) / 2) * spacing + col * spacing;
                const z = row === 0 ? -1.5 : 1.5;
                
                spindle.position.set(x, 2.5, z);
                spindle.userData = {
                    type: 'spindle',
                    name: `锭子 ${spindleIndex + 1}`,
                    description: '用于纺纱的锭子，通过皮带带动高速旋转，将纤维加捻成纱线。',
                    index: spindleIndex + 1,
                    speed: '约80-150 rpm',
                    material: '竹木',
                    height: '约30厘米'
                };
                
                this.spindles.push(spindle);
                this.spindleGroup.add(spindle);
            }
        }

        this.spindleGroup.position.set(0, 0, 0);
        this.group.add(this.spindleGroup);
    }

    createSingleSpindle(spindleMaterial, baseMaterial, index) {
        const spindle = new THREE.Group();

        const baseGeometry = new THREE.CylinderGeometry(0.15, 0.18, 0.3, 12);
        const base = new THREE.Mesh(baseGeometry, baseMaterial);
        base.position.y = 0.15;
        base.castShadow = true;
        spindle.add(base);

        const shaftGeometry = new THREE.CylinderGeometry(0.04, 0.04, 0.6, 8);
        const shaft = new THREE.Mesh(shaftGeometry, spindleMaterial);
        shaft.position.y = 0.6;
        shaft.castShadow = true;
        spindle.add(shaft);

        const whorlGeometry = new THREE.CylinderGeometry(0.12, 0.12, 0.08, 16);
        const whorl = new THREE.Mesh(whorlGeometry, spindleMaterial);
        whorl.position.y = 0.4;
        whorl.castShadow = true;
        spindle.add(whorl);

        const tipGeometry = new THREE.ConeGeometry(0.04, 0.15, 8);
        const tip = new THREE.Mesh(tipGeometry, spindleMaterial);
        tip.position.y = 0.97;
        tip.castShadow = true;
        spindle.add(tip);

        const bobbinGeometry = new THREE.CylinderGeometry(0.08, 0.08, 0.3, 12);
        const bobbinMaterial = new THREE.MeshStandardMaterial({
            color: 0xf5deb3,
            roughness: 0.9,
            metalness: 0
        });
        const bobbin = new THREE.Mesh(bobbinGeometry, bobbinMaterial);
        bobbin.position.y = 0.65;
        bobbin.castShadow = true;
        spindle.add(bobbin);

        spindle.userData.spindleShaft = shaft;
        spindle.userData.bobbin = bobbin;
        spindle.userData.baseRotationSpeed = 0.8 + Math.random() * 0.4;

        return spindle;
    }

    createYarns() {
        this.yarnGroup = new THREE.Group();
        this.yarnGroup.userData = { type: 'yarn', name: '纱线', description: '由32个锭子纺出的纱线，汇集到上方的导纱装置。' };

        const yarnMaterial = new THREE.LineBasicMaterial({
            color: 0xf5deb3,
            transparent: true,
            opacity: 0.8
        });

        this.yarns = [];

        for (let i = 0; i < this.spindles.length; i++) {
            const spindle = this.spindles[i];
            const curve = new THREE.CatmullRomCurve3([
                new THREE.Vector3(0, 0, 0),
                new THREE.Vector3(0, 0.5, 0),
                new THREE.Vector3(0, 1, 0),
                new THREE.Vector3(0, 1.5, 0)
            ]);

            const tubeGeometry = new THREE.TubeGeometry(curve, 20, 0.015, 8, false);
            const yarnMesh = new THREE.Mesh(tubeGeometry, yarnMaterial.clone());
            yarnMesh.position.copy(spindle.position);
            yarnMesh.position.y += 0.9;
            
            yarnMesh.userData = {
                spindleIndex: i,
                originalY: spindle.position.y + 0.9
            };

            this.yarns.push(yarnMesh);
            this.yarnGroup.add(yarnMesh);
        }

        this.group.add(this.yarnGroup);
    }

    updateYarns(time, speedFactor) {
        if (!this.showYarn) return;

        for (let i = 0; i < this.yarns.length; i++) {
            const yarn = this.yarns[i];
            const spindle = this.spindles[i];
            
            const waveOffset = i * 0.3;
            const wave = Math.sin(time * 3 + waveOffset) * 0.05 * speedFactor;
            
            const curvePoints = [
                new THREE.Vector3(
                    spindle.position.x + wave * 0.3,
                    0,
                    spindle.position.z + wave * 0.2
                ),
                new THREE.Vector3(
                    spindle.position.x + wave * 0.5,
                    0.5,
                    spindle.position.z + wave * 0.3
                ),
                new THREE.Vector3(
                    spindle.position.x + wave * 0.3,
                    1,
                    spindle.position.z + wave * 0.15
                ),
                new THREE.Vector3(
                    spindle.position.x + wave * 0.1,
                    1.8,
                    0
                )
            ];

            const curve = new THREE.CatmullRomCurve3(curvePoints);
            const newGeometry = new THREE.TubeGeometry(curve, 30, 0.012, 6, false);
            
            yarn.geometry.dispose();
            yarn.geometry = newGeometry;
        }
    }

    update(delta, wheelSpeed) {
        this.time += delta;
        const speedFactor = wheelSpeed / 50;

        this.wheelRotation += delta * (wheelSpeed * 0.1) * 0.2;
        if (this.wheelGroup) {
            this.wheelGroup.rotation.z = -this.wheelRotation;
        }

        if (this.mainShaft) {
            this.mainShaft.rotation.x = this.wheelRotation * 3.5;
        }

        this.spindleRotation += delta * (wheelSpeed * 0.1) * 3.5;
        this.spindles.forEach((spindle, index) => {
            const baseSpeed = spindle.userData.baseRotationSpeed;
            spindle.rotation.y = this.spindleRotation * baseSpeed;
        });

        this.updateYarns(this.time, speedFactor);
    }

    setYarnVisible(visible) {
        this.showYarn = visible;
        this.yarnGroup.visible = visible;
    }

    getClickableObjects() {
        const objects = [];
        if (this.wheelGroup) objects.push(this.wheelGroup);
        if (this.frameGroup) objects.push(this.frameGroup);
        if (this.mainShaft) objects.push(this.mainShaft);
        if (this.yarnGroup) objects.push(this.yarnGroup);
        objects.push(...this.spindles);
        return objects;
    }

    getSpindleSpeed(wheelSpeed) {
        return wheelSpeed * 3.5;
    }

    getTension(wheelSpeed) {
        return 5 + wheelSpeed * 0.15;
    }

    getTwist(wheelSpeed) {
        return 20 + wheelSpeed * 0.8;
    }

    getPower(wheelSpeed) {
        return 0.5 + wheelSpeed * 0.015;
    }
}
