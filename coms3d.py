import mph
import numpy as np


class ComsolModel:

    def __init__(
        self, client, inl1U0=0.15, inl2U0=0.15, hmaxsiz=14, hminsiz=0.15, outout=42
    ,fil = [False,200]):
        self.inl1U0 = inl1U0
        self.inl2U0 = inl2U0
        self.hmaxsiz = str(hmaxsiz)
        self.hminsiz = str(hminsiz)
        self.outout = outout
        self.client = client
        self.model = self.client.create("Model")
        self.java_model = self.model.java
        self.allmodel = self.java_model.component().create("comp1", True)
        self.fil = fil
    def combuild(self):
        geom = self.allmodel.geom()
        geom1 = geom.create("geom1", 3)
        geom1.lengthUnit("um")
        wp1 = geom1.create("wp1", "WorkPlane")
        wp1.geom().create("imp1", "Import")
        wp1.geom().feature("imp1").set("type", "dxf")
        wp1.geom().feature("imp1").set("filename", "./docouter.dxf")
        col = "imp1"
        if self.fil[0] == True:
            wp1.geom().create("fil1", "Fillet")
            wp1.geom().feature("fil1").selection("point").set("imp1(1)", 8, 9)
            wp1.geom().feature("fil1").set("radius", self.fil[1])
            col = "fil1"
            self.outout = self.outout + 2

        wp1.geom().create("csol1", "ConvertToSolid")
        wp1.geom().feature("csol1").selection("input").set(col)

        wp1.geom().create("imp2", "Import")
        wp1.geom().feature("imp2").set("type", "dxf")
        wp1.geom().feature("imp2").set("filename", "./docinter.dxf")

        wp1.geom().create("csol2", "ConvertToSolid")
        wp1.geom().feature("csol2").selection("input").set("imp2")

        wp1.geom().create("dif1", "Difference")
        wp1.geom().feature("dif1").selection("input").set("csol1")
        wp1.geom().feature("dif1").selection("input2").set("csol2")

        geom1.create("ext1", "Extrude")
        geom1.feature("ext1").setIndex("distance", "80", 0)
        geom1.feature("ext1").selection("input").set("wp1")
        geom1.run()

        material = self.allmodel.material()
        material.create("mat1", "Common")
        mat1 = self.allmodel.material("mat1")
        mat1.label("wa")
        mat1.materialType("nonSolid")
        mat1.propertyGroup("def").set("density", 1000.0)
        mat1.propertyGroup("def").set("dynamicviscosity", 1e-3)

        material.create("mat2", "Common")
        mat2 = self.allmodel.material("mat2")
        mat2.label("ea")
        mat2.materialType("nonSolid")
        mat2.selection().geom("geom1", 2)
        mat2.selection().set(2)
        mat2.propertyGroup("def").set("density", 1000.0)
        mat2.propertyGroup("def").set("dynamicviscosity", 1e-3)

        spf = self.allmodel.physics().create("spf", "LaminarFlow", "geom1")
        spf.create("inl1", "InletBoundary", 2)
        spf.feature("inl1").selection().set(5)
        spf.create("inl2", "InletBoundary", 2)
        spf.feature("inl2").selection().set(2)
        spf.create("out1", "OutletBoundary", 2)
        spf.feature("out1").selection().set(self.outout)
        spf.feature("inl1").set("U0in", self.inl1U0)
        spf.feature("inl2").set("U0in", self.inl2U0)

        tds = self.allmodel.physics().create("tds", "DilutedSpecies", [["c"]])
        tds.feature("cdm1").set(
            "D_c",
            [
                "1e-9[m^2/s]",
                "0",
                "0",
                "0",
                "1e-9[m^2/s]",
                "0",
                "0",
                "0",
                "1e-9[m^2/s]",
            ],
        )
        tds.create("conc1", "Concentration", 2)
        tds.feature("conc1").selection().set(5)
        tds.create("conc2", "Concentration", 2)
        tds.feature("conc2").selection().set(2)
        tds.feature("conc1").setIndex("species", 1.0, 0)
        tds.feature("conc2").setIndex("species", 1.0, 0)
        tds.create("out1", "Outflow", 2)
        tds.feature("out1").selection().set(self.outout)
        tds.feature("conc2").setIndex("c0", 1.0, 0)

        self.allmodel.multiphysics().create("rfd1", "ReactingFlowDS", 3)

        mesh = self.allmodel.mesh().create("mesh1")
        # mesh.create("fq1", "FreeQuad")
        mesh.create("ftet1", "FreeTet")
        mesh.feature("size").set("hmax", self.hmaxsiz)
        mesh.feature("size").set("hgrad", 1.3)
        mesh.feature("size").set("hmin", self.hminsiz)
        # bl1 = mesh.create("bl1", "BndLayer")
        # bl1.selection().geom(2)
        # bl1.selection().set()
        # bl1.selection().allGeom()
        # bl1.create("blp1", "BndLayerProp")
        # bl1.feature("blp1").selection().all()
        # bl1.feature("blp1").set("blnlayers", '3')

        mesh.run()

        bnd = self.allmodel.probe().create("bnd1", "Boundary")
        bnd.selection().set(self.outout)
        bnd.set("expr", "c")

        setdcase = self.java_model.study().create("std1")
        setdcase.feature().create("stat", "Stationary")
        setdcase.run()

        self.java_model.result().numerical().create("av1", "AvSurface")
        self.java_model.result().numerical("av1").selection().set(self.outout)
        self.java_model.result().numerical("av1").set(
            "expr", ["(c-bnd1)^2", "p", "spf.U"]
        )

        self.java_model.result().numerical().create("av2", "AvSurface")
        self.java_model.result().numerical("av2").selection().set(2)
        self.java_model.result().numerical("av2").set("expr", ["p", "spf.U"])

        self.java_model.result().numerical().create("int1", "IntSurface")
        self.java_model.result().numerical("int1").selection().set(self.outout)
        self.java_model.result().numerical("int1").set("expr", ["spf.U"])

        self.java_model.result().numerical().run()

        # data = self.model.evaluate(["av1", "av2", "int1"])

        # print(data)

        return self.model

    def get_meshin(self):

        data = self.model.evaluate(["x", "y", "c", "spf.U", "p"])
        indices = np.where(data[1] == np.min(data[1]))

        outdices = np.where(data[0] == np.max(data[0]))
        inin = [array[indices] for array in data]
        inin = [d[np.argsort(inin[0])] for d in inin]
        ouou = [array[outdices] for array in data]
        ouou = [d[np.argsort(ouou[1])] for d in ouou]

        cout_x = ouou[1]
        cout = ouou[2]
        uout = ouou[3]

        return (
            cout_x,
            cout,
            uout
        )

    def meshin(self, fname):

        javamodel = self.combuild().java

        CutL = javamodel.result().dataset().create("cln2", "CutLine3D")
        CutL.set("method", "pointdir")
        CutL.set("pdpoint", [2900.0, 400.0, 35.0])
        CutL.set("pddir", [0, 1.0, 0])

        exda = javamodel.result().export().create("data1", "Data")
        exda.set("data", "cln2")
        exda.set("filename", fname)
        exda.set("header", False)
        # exda.set("fullprec", False)
        exda.set("sort", True)
        exda.set("expr", ["spf.U", "c"])
        # self.model.save("123.mph")
        exda.run()
        self.client.remove(self.model)

    def get_mixing_index(self):

        datamodel = self.combuild()
        cp1 = datamodel / "evaluations/Surface Average 1"
        cp2 = datamodel / "evaluations/Surface Average 2"
        cp3 = datamodel / "evaluations/Surface Integration 1"
        cp = [cp1,cp2,cp3]

        data = [np.array(j.java.getReal()).squeeze() for j in cp]

        csa_out = data[0][0]
        usa_out = data[0][2]

        poutin = data[1][0] - data[0][1]

        usa_in = data[1][1]
        usf_out = data[2]*1000000000
        cmean = datamodel.evaluate(["bnd1"])
        self.client.remove(datamodel)

        return cmean,csa_out, usa_out, poutin, usa_in, usf_out
