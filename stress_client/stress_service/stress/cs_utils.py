import numpy as np
from sectionproperties.pre.geometry import Polygon
from sectionproperties.pre.geometry import Geometry
from sectionproperties.analysis.section import Section
import base64
from io import BytesIO
import matplotlib.pyplot as plt
from matplotlib.patches import Rectangle, Circle
from matplotlib.collections import PatchCollection


class BaseSquare:
    # def __init__(self, *args, **kwargs):
    #     print('args: ', args, 'kwargs: ', kwargs)
    #     self.x = kwargs['width'] if len(kwargs) > 0 else args[0]['width']
    #     self.y = kwargs['height'] if len(kwargs) > 0 else args[0]['height']
    #     self.area = self.x * self.y
    #     self.div_x = kwargs['div_x'] if len(kwargs) > 0 else args[0]['div_x']
    #     self.div_y = kwargs['div_y'] if len(kwargs) > 0 else args[0]['div_y']
    #     self.alpha = kwargs['alpha'] if len(kwargs) > 0 else args[0]['alpha']
    def __init__(self, x, y, div_x, div_y, alpha):
        self.x = x
        self.y = y
        self.area = x * y
        self.div_x = div_x
        self.div_y = div_y
        self.alpha = alpha

    @property
    def cog(self):
        return (self.x * np.cos(self.alpha) - self.y * np.sin(self.alpha)) / 2 + self.div_x, \
            (self.x * np.sin(self.alpha) + self.y * np.cos(self.alpha)) / 2 + self.div_y

    @property
    def inertia(self):
        # self inertia property Ix, Iy, Ixy, J regards origin and in global CS
        _a, _b = min(self.x, self.y), max(self.x, self.y)
        _x = _b / _a
        _coeff = 0.32 if _x > 10 else -0.000148*_x**4 + 0.0039*_x**3 - 0.0376*_x**2 + 0.1635*_x + 0.0152
        _inertia_x = self.x * (self.y**3) / 12
        _inertia_y = self.y * (self.x**3) / 12
        # rotate axis in global CS
        lst = self.inertia_axis(area=self.area, mom_inertia=(_inertia_x, _inertia_y, 0),
                                div_x=0, div_y=0, cog=False, angle_rotate=-self.alpha)
        # recalculate property regarding origin point (0, 0)
        lst = self.inertia_axis(area=self.area, mom_inertia=lst[-3:],
                                div_x=self.cog[0], div_y=self.cog[1], cog=False, angle_rotate=0)
        inertia_x, inertia_y, inertia_xy = lst[-3:]
        return inertia_x, inertia_y, inertia_xy, _coeff * _b * _a ** 3


    @staticmethod
    def inertia_axis(area=0, mom_inertia=[], div_x=0, div_y=0, cog=False, angle_rotate=0):
        #recalculation moment of inertia in another axis
        k = -1 if cog else 1
        mom_inertia_x = mom_inertia[0] + k * area * (div_y ** 2)
        mom_inertia_y = mom_inertia[1] + k * area * (div_x ** 2)
        mom_inertia_xy = mom_inertia[2] + k * area * (div_x * div_y)
        alpha = np.arctan(2 * mom_inertia_xy/(mom_inertia_x-mom_inertia_y + mom_inertia_y/1e12)) / 2 \
            if cog else angle_rotate
        inertia_1 = mom_inertia_x * (np.cos(k*alpha)**2) + mom_inertia_y * (np.sin(k*alpha)**2) - \
                    mom_inertia_xy * np.sin(k*alpha*2)
        inertia_2 = mom_inertia_x * (np.sin(k*alpha)**2) + mom_inertia_y * (np.cos(k*alpha)**2) + \
                    mom_inertia_xy * np.sin(k*alpha*2)
        inertia_12 = (mom_inertia_x - mom_inertia_y) * np.sin(k*alpha*2) / 2 + \
                     mom_inertia_xy * np.cos(2*k*alpha)
        return mom_inertia_x, mom_inertia_y, mom_inertia_xy, alpha, inertia_1, inertia_2, inertia_12

    @property
    def output(self):
        return dict(zip(('area', 'cog', 'inertia'), (self.area, self.cog, self.inertia)))

    @property
    def pre_plot(self):
        return Rectangle((self.div_x, self.div_y), self.x, self.y, self.alpha * 180 / np.pi, linewidth=2, edgecolor='r',
                         facecolor='none')
                         # from matplot version 3.7 facecolor='none', rotation_point=(self.div_x, self.div_y))

class BaseSegment:
    def __init__(self, radius, seg_angle, div_x, div_y, alpha):
        self.radius = radius
        self.seg_angle = seg_angle / 2
        self.div_x, self.div_y, self.alpha = div_x, div_y, alpha
        self.area = self.seg_angle * radius ** 2

    @property
    def cog(self):
        return self.div_x, self.div_y + 2 / 3 * self.radius * np.sin(self.seg_angle) / self.seg_angle

    @property
    def inertia(self):
        return (self.radius ** 4 / 8 * (2 * self.seg_angle + np.sin(self.seg_angle) -
                32 * np.sin(self.seg_angle)**2 / (9 * self.seg_angle)) + self.area * self.cog[1] ** 2,
                self.radius ** 4 / 8 * (2 * self.seg_angle - np.sin(self.seg_angle)) + + self.area * self.cog[0] ** 2,
                self.area * self.cog[0] * self.cog[1])


class AnySections:
    def __init__(self, *args, **kwargs):
        if 'square' in kwargs:
            self.squares = [BaseSquare(*_square) for _square in kwargs['square']]
            self.alpha = kwargs['square'][0][-1]

    @property
    def area(self):
        return sum(_square.area for _square in self.squares)

    @property
    def cog(self):
        return tuple(
            sum(_square.area * _square.cog[_idx] for _square in self.squares) / self.area for _idx in range(2))

    @property
    def inertia(self):
        _inertia_list = list(map(sum, zip(*[_square.inertia for _square in self.squares])))
        _inertia_list += BaseSquare.inertia_axis(area=self.area,
                                                 mom_inertia=_inertia_list,
                                                 div_x=self.cog[0],
                                                 div_y=self.cog[1],
                                                 cog=True,
                                                 angle_rotate=0)
        _inertia_list[-4] = - np.rad2deg(_inertia_list[-4])
        # change coordinate system from
        # 'Ixx', 'Iyy', 'Ixy', 'J', 'Ixx_cog', 'Iyy_cog', 'Ixy_cog', 'alpha', 'Imax_princ', 'Imin_princ'
        # to 'Iyy', 'Izz', 'Iyz', 'J', 'Iyy_cog', 'Izz_cog', 'Iyz_cog', 'alpha', 'Imax_princ', 'Imin_princ'
        return dict(zip(('Iyy', 'Izz', 'Iyz', 'J', 'Iyy_cog', 'Izz_cog', 'Iyz_cog', 'alpha', 'Imain_1',
                         'Imain_2', 'I0'), _inertia_list))

    @property
    def output(self):
        output_dct = dict(zip(('area', 'cog_Y', 'cog_Z'), (self.area, *self.cog)))
        output_dct.update(self.inertia)
        return output_dct

    @property
    def plot(self):
        path = PatchCollection([i.pre_plot for i in self.squares])
        path.set(linewidth=2, edgecolor='k', alpha=0.3)
        fig, ax = plt.subplots()
        ax.add_collection(path)
        ax.scatter(*self.cog, c="r", marker="x", s=100, label="Center of gravity")
        axis_angle = np.radians(self.inertia['alpha']) #+ self.alpha
        ax.axline(self.cog, slope=np.tan(axis_angle), color="black", linestyle="--")
        ax.axline(self.cog, slope=np.tan(axis_angle + 1.5708), color="black", linestyle="--")
        ax.autoscale()
        ax.set_aspect('equal',  adjustable='box')
        ax.legend(loc="lower left", bbox_to_anchor=(0, 1))
        image = BytesIO()
        fig.savefig(image, format='png')
        image.seek(0)
        decode = base64.b64encode(image.getvalue()).decode('utf8')
        img_data = f"data:image/png;base64,{decode}"
        return img_data

    def self_prepare(self, *args, **kwargs):
        dct = kwargs if len(kwargs) > 0 else args[0]
        if 'div_z' in dct:
            dct['div_x'], dct['div_y'] = dct['div_y'], dct['div_z']
        dct['alpha'] = np.radians(dct['alpha'])
        [setattr(self, attr, dct[attr]) for attr in dct]

    @staticmethod
    def div_rotate(div_x, div_y, x, y, alpha):
        return div_x + x * np.cos(alpha) - y * np.sin(alpha), div_y + y * np.cos(alpha) + x * np.sin(alpha)


class Square(AnySections):
    def __init__(self, *args, **kwargs):
        self.self_prepare(*args, **kwargs)
        super().__init__(square=[(self.width_1, self.height, self.div_x, self.div_y, self.alpha)])


class AngleSection(AnySections):
    # def __init__(self, height, width, th_1, th_2, div_x=0, div_y=0, alpha=0, dct={}):
    def __init__(self, *args, **kwargs):
        self.self_prepare(*args, **kwargs)
        super().__init__(square=[(self.th_1, self.height, self.div_x, self.div_y, self.alpha), #vertical
                                 (self.width_1 - self.th_1, self.th_2, self.div_x + self.th_1 * np.cos(self.alpha),
                                  self.div_y + self.th_1 * np.sin(self.alpha), #horizontal
                                  self.alpha)])


class CSection(AnySections):
    # def __init__(self, width_1, height, width_2, th_1, th_2, th_3, div_x=0, div_y=0, alpha=0):
    def __init__(self, *args, **kwargs):
        self.self_prepare(*args, **kwargs)
        super().__init__(square=[(self.width_1, self.th_1,
                                  *self.div_rotate(self.div_x, self.div_y, 0, self.height - self.th_1, self.alpha),
                                  self.alpha), # upper flange
                                 (self.th_2, self.height - self.th_1 - self.th_3,
                                  *self.div_rotate(self.div_x, self.div_y, 0, self.th_3, self.alpha), self.alpha), # web
                                 (self.width_2, self.th_3, self.div_x, self.div_y, self.alpha)  # lower flange
                                 ])


class ISection(AnySections):
    # def __init__(self, width_1, height, width_2, th_1, th_2, th_3, div_x=0, div_y=0, alpha=0):
    def __init__(self, *args, **kwargs):
        self.self_prepare(*args, **kwargs)
        super().__init__(square=[(self.width_1, self.th_1,
                                  *self.div_rotate(self.div_x, self.div_y, (self.width_2 - self.width_1) / 2,
                                                  (self.height-self.th_1), self.alpha),
                                  self.alpha), # upper flange
                                 (self.th_2, self.height - self.th_1 - self.th_3,
                                  *self.div_rotate(self.div_x, self.div_y, (self.width_2 - self.th_2) / 2, self.th_3,
                                                   self.alpha), self.alpha), # web
                                 (self.width_2, self.th_3, self.div_x, self.div_y, self.alpha)  # lower flange
                                 ])


class ZSection(AnySections):
    # def __init__(self, width_1, height, width_2, th_1, th_2, th_3, div_x=0, div_y=0, alpha=0):
    def __init__(self, *args, **kwargs):
        self.self_prepare(*args, **kwargs)
        super().__init__(square=[(self.width_1, self.th_1,
                                  *self.div_rotate(self.div_x, self.div_y, self.width_2 - self.th_2,
                                                   self.height - self.th_1, self.alpha), self.alpha), # upper flange
                                 (self.th_2, self.height - self.th_1 - self.th_3,
                                  *self.div_rotate(self.div_x, self.div_y, self.width_2 - self.th_2, self.th_3,
                                                   self.alpha), self.alpha), # web
                                 (self.width_2, self.th_3, self.div_x, self.div_y, self.alpha)  # lower flange
                                 ])


class FemPolygon:
    # Taken from open source
    def __init__(self, points_lst: list):
        self.polygon = Polygon(points_lst)
        self.geometry = Geometry(self.polygon)
        self.geometry.create_mesh(mesh_sizes=[self.polygon.area/100])
        self.section = Section(self.geometry)


    @property
    def output(self) -> dict:
        test_property = self.section.calculate_frame_properties()
        return dict(zip(('area', 'Iyy', 'Izz', 'Iyz', 'J', 'phi'), test_property))

    @property
    def plot(self) -> dict:
        self.section.calculate_geometric_properties()
        figure = self.section.plot_centroids(render=False).get_figure()
        image = BytesIO()
        figure.savefig(image, format='png')

        image.seek(0)
        decode = base64.b64encode(image.getvalue()).decode('utf8')
        img_data = f"data:image/png;base64,{decode}"
        return img_data
