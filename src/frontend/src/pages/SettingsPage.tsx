import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '../components/ui/card';
import { Button } from '../components/ui/button';
import { Input } from '../components/ui/input';
import { Label } from '../components/ui/label';
import { Badge } from '../components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from '../components/ui/tabs';
import { 
  MapPin, 
  School,
  Plus,
  Edit,
  Trash2,
  Save,
  X
} from 'lucide-react';

const initialRegions = [
  { id: 1, name: 'Prague East', code: 'PRG-E', schools: 12, active: true },
  { id: 2, name: 'Prague West', code: 'PRG-W', schools: 9, active: true },
  { id: 3, name: 'Central Bohemia', code: 'CB', schools: 15, active: true },
  { id: 4, name: 'South Moravia', code: 'SM', schools: 11, active: true },
  { id: 5, name: 'Hradec Králové', code: 'HK', schools: 8, active: true },
  { id: 6, name: 'Plzeň', code: 'PLZ', schools: 7, active: true },
  { id: 7, name: 'Liberec', code: 'LBC', schools: 6, active: true },
  { id: 8, name: 'Olomouc', code: 'OLO', schools: 5, active: false },
];

const initialSchools = [
  { id: 1, name: 'Gymnasium Brandýs', region: 'Prague East', type: 'Gymnasium', students: 456, active: true },
  { id: 2, name: 'ZŠ Kolín', region: 'Central Bohemia', type: 'Primary', students: 324, active: true },
  { id: 3, name: 'ZŠ Černošice', region: 'Prague West', type: 'Primary', students: 289, active: true },
  { id: 4, name: 'Gymnázium HK', region: 'Hradec Králové', type: 'Gymnasium', students: 412, active: true },
  { id: 5, name: 'ZŠ Plzeň 3', region: 'Plzeň', type: 'Primary', students: 367, active: true },
  { id: 6, name: 'ZŠ Benátky', region: 'Prague East', type: 'Primary', students: 298, active: true },
];

export function SettingsPage() {
  const [regions, setRegions] = useState(initialRegions);
  const [schools, setSchools] = useState(initialSchools);
  const [isAddingRegion, setIsAddingRegion] = useState(false);
  const [isAddingSchool, setIsAddingSchool] = useState(false);
  const [newRegion, setNewRegion] = useState({ name: '', code: '' });
  const [newSchool, setNewSchool] = useState({ name: '', region: '', type: '', students: '' });

  const handleAddRegion = () => {
    if (newRegion.name && newRegion.code) {
      const region = {
        id: regions.length + 1,
        name: newRegion.name,
        code: newRegion.code,
        schools: 0,
        active: true
      };
      setRegions([...regions, region]);
      setNewRegion({ name: '', code: '' });
      setIsAddingRegion(false);
    }
  };

  const handleAddSchool = () => {
    if (newSchool.name && newSchool.region && newSchool.type) {
      const school = {
        id: schools.length + 1,
        name: newSchool.name,
        region: newSchool.region,
        type: newSchool.type,
        students: parseInt(newSchool.students) || 0,
        active: true
      };
      setSchools([...schools, school]);
      setNewSchool({ name: '', region: '', type: '', students: '' });
      setIsAddingSchool(false);
    }
  };

  const toggleRegionStatus = (id: number) => {
    setRegions(regions.map(r => 
      r.id === id ? { ...r, active: !r.active } : r
    ));
  };

  const toggleSchoolStatus = (id: number) => {
    setSchools(schools.map(s => 
      s.id === id ? { ...s, active: !s.active } : s
    ));
  };

  return (
    <div className="space-y-6">
      <div>
        <h1>Settings</h1>
        <p className="text-slate-600 mt-1">Manage regions, schools, and platform configuration</p>
      </div>

      <Tabs defaultValue="regions" className="space-y-6">
        <TabsList>
          <TabsTrigger value="regions">Regions</TabsTrigger>
          <TabsTrigger value="schools">Schools</TabsTrigger>
          <TabsTrigger value="metadata">Metadata</TabsTrigger>
        </TabsList>

        <TabsContent value="regions" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>Region Management</CardTitle>
                  <p className="text-sm text-slate-600 mt-1">Add and configure regions</p>
                </div>
                <Button onClick={() => setIsAddingRegion(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add Region
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isAddingRegion && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <Label>Region Name</Label>
                      <Input
                        placeholder="e.g., South Bohemia"
                        value={newRegion.name}
                        onChange={(e) => setNewRegion({ ...newRegion, name: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                    <div>
                      <Label>Region Code</Label>
                      <Input
                        placeholder="e.g., SB"
                        value={newRegion.code}
                        onChange={(e) => setNewRegion({ ...newRegion, code: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleAddRegion}>
                      <Save className="w-4 h-4 mr-2" />
                      Save Region
                    </Button>
                    <Button variant="outline" onClick={() => setIsAddingRegion(false)}>
                      <X className="w-4 h-4 mr-2" />
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              <div className="space-y-3">
                {regions.map((region) => (
                  <div
                    key={region.id}
                    className="flex items-center justify-between p-4 bg-slate-50 rounded-lg hover:bg-slate-100 transition-colors"
                  >
                    <div className="flex items-center gap-4">
                      <div className="w-10 h-10 bg-blue-100 rounded-lg flex items-center justify-center">
                        <MapPin className="w-5 h-5 text-blue-600" />
                      </div>
                      <div>
                        <div className="flex items-center gap-2">
                          <span>{region.name}</span>
                          <Badge variant="outline" className="text-xs">
                            {region.code}
                          </Badge>
                          {region.active ? (
                            <Badge className="bg-green-100 text-green-700 hover:bg-green-100 text-xs">
                              Active
                            </Badge>
                          ) : (
                            <Badge className="bg-slate-200 text-slate-700 hover:bg-slate-200 text-xs">
                              Inactive
                            </Badge>
                          )}
                        </div>
                        <p className="text-sm text-slate-600 mt-0.5">
                          {region.schools} schools
                        </p>
                      </div>
                    </div>
                    <div className="flex items-center gap-2">
                      <Button variant="outline" size="sm">
                        <Edit className="w-4 h-4 mr-1" />
                        Edit
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={() => toggleRegionStatus(region.id)}
                      >
                        {region.active ? 'Deactivate' : 'Activate'}
                      </Button>
                    </div>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Total Regions</p>
                  <p className="text-3xl">{regions.length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Active Regions</p>
                  <p className="text-3xl text-green-600">{regions.filter(r => r.active).length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Total Schools</p>
                  <p className="text-3xl text-blue-600">{regions.reduce((acc, r) => acc + r.schools, 0)}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="schools" className="space-y-6">
          <Card>
            <CardHeader>
              <div className="flex items-center justify-between">
                <div>
                  <CardTitle>School Management</CardTitle>
                  <p className="text-sm text-slate-600 mt-1">Add and configure schools</p>
                </div>
                <Button onClick={() => setIsAddingSchool(true)}>
                  <Plus className="w-4 h-4 mr-2" />
                  Add School
                </Button>
              </div>
            </CardHeader>
            <CardContent>
              {isAddingSchool && (
                <div className="mb-6 p-4 bg-blue-50 border border-blue-200 rounded-lg">
                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
                    <div>
                      <Label>School Name</Label>
                      <Input
                        placeholder="e.g., Gymnázium Brno"
                        value={newSchool.name}
                        onChange={(e) => setNewSchool({ ...newSchool, name: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                    <div>
                      <Label>Region</Label>
                      <Input
                        placeholder="e.g., South Moravia"
                        value={newSchool.region}
                        onChange={(e) => setNewSchool({ ...newSchool, region: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                    <div>
                      <Label>School Type</Label>
                      <Input
                        placeholder="e.g., Gymnasium or Primary"
                        value={newSchool.type}
                        onChange={(e) => setNewSchool({ ...newSchool, type: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                    <div>
                      <Label>Number of Students</Label>
                      <Input
                        type="number"
                        placeholder="e.g., 350"
                        value={newSchool.students}
                        onChange={(e) => setNewSchool({ ...newSchool, students: e.target.value })}
                        className="mt-1.5"
                      />
                    </div>
                  </div>
                  <div className="flex gap-2">
                    <Button onClick={handleAddSchool}>
                      <Save className="w-4 h-4 mr-2" />
                      Save School
                    </Button>
                    <Button variant="outline" onClick={() => setIsAddingSchool(false)}>
                      <X className="w-4 h-4 mr-2" />
                      Cancel
                    </Button>
                  </div>
                </div>
              )}

              <div className="overflow-x-auto">
                <table className="w-full">
                  <thead>
                    <tr className="border-b border-slate-200">
                      <th className="text-left py-3 px-4">School Name</th>
                      <th className="text-left py-3 px-4">Region</th>
                      <th className="text-left py-3 px-4">Type</th>
                      <th className="text-left py-3 px-4">Students</th>
                      <th className="text-left py-3 px-4">Status</th>
                      <th className="text-right py-3 px-4">Actions</th>
                    </tr>
                  </thead>
                  <tbody>
                    {schools.map((school) => (
                      <tr key={school.id} className="border-b border-slate-100 hover:bg-slate-50">
                        <td className="py-3 px-4">
                          <div className="flex items-center gap-2">
                            <School className="w-4 h-4 text-blue-600" />
                            <span>{school.name}</span>
                          </div>
                        </td>
                        <td className="py-3 px-4 text-sm text-slate-600">{school.region}</td>
                        <td className="py-3 px-4">
                          <Badge variant="outline" className="text-xs">
                            {school.type}
                          </Badge>
                        </td>
                        <td className="py-3 px-4 text-sm">{school.students}</td>
                        <td className="py-3 px-4">
                          {school.active ? (
                            <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                              Active
                            </Badge>
                          ) : (
                            <Badge className="bg-slate-200 text-slate-700 hover:bg-slate-200">
                              Inactive
                            </Badge>
                          )}
                        </td>
                        <td className="py-3 px-4">
                          <div className="flex items-center justify-end gap-2">
                            <Button variant="outline" size="sm">
                              <Edit className="w-3 h-3 mr-1" />
                              Edit
                            </Button>
                            <Button
                              variant="outline"
                              size="sm"
                              onClick={() => toggleSchoolStatus(school.id)}
                            >
                              {school.active ? 'Deactivate' : 'Activate'}
                            </Button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </tbody>
                </table>
              </div>
            </CardContent>
          </Card>

          <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Total Schools</p>
                  <p className="text-3xl">{schools.length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Active Schools</p>
                  <p className="text-3xl text-green-600">{schools.filter(s => s.active).length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Gymnasium</p>
                  <p className="text-3xl text-blue-600">{schools.filter(s => s.type === 'Gymnasium').length}</p>
                </div>
              </CardContent>
            </Card>
            <Card>
              <CardContent className="pt-6">
                <div className="text-center">
                  <p className="text-sm text-slate-600 mb-2">Primary Schools</p>
                  <p className="text-3xl text-purple-600">{schools.filter(s => s.type === 'Primary').length}</p>
                </div>
              </CardContent>
            </Card>
          </div>
        </TabsContent>

        <TabsContent value="metadata" className="space-y-6">
          <Card>
            <CardHeader>
              <CardTitle>Platform Metadata</CardTitle>
              <p className="text-sm text-slate-600">Configure platform-wide settings</p>
            </CardHeader>
            <CardContent className="space-y-6">
              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <Label>Platform Name</Label>
                  <Input defaultValue="SchoolInsights" className="mt-1.5" />
                </div>
                <div>
                  <Label>Organization</Label>
                  <Input defaultValue="Nadace The Foundation" className="mt-1.5" />
                </div>
                <div>
                  <Label>Default Region</Label>
                  <Input defaultValue="Prague East" className="mt-1.5" />
                </div>
                <div>
                  <Label>Academic Year</Label>
                  <Input defaultValue="2025/2026" className="mt-1.5" />
                </div>
              </div>

              <div className="pt-6 border-t border-slate-200">
                <h3 className="mb-4">Data Quality Thresholds</h3>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                  <div>
                    <Label>Excellent (Green)</Label>
                    <Input type="number" defaultValue="90" className="mt-1.5" />
                    <p className="text-xs text-slate-500 mt-1">Score ≥ 90%</p>
                  </div>
                  <div>
                    <Label>Good (Yellow)</Label>
                    <Input type="number" defaultValue="75" className="mt-1.5" />
                    <p className="text-xs text-slate-500 mt-1">Score 75-89%</p>
                  </div>
                  <div>
                    <Label>Poor (Red)</Label>
                    <Input type="number" defaultValue="75" className="mt-1.5" />
                    <p className="text-xs text-slate-500 mt-1">Score &lt; 75%</p>
                  </div>
                </div>
              </div>

              <div className="pt-6 border-t border-slate-200">
                <h3 className="mb-4">File Upload Settings</h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                  <div>
                    <Label>Max File Size (MB)</Label>
                    <Input type="number" defaultValue="50" className="mt-1.5" />
                  </div>
                  <div>
                    <Label>Allowed File Types</Label>
                    <Input defaultValue="xlsx, csv, json, txt, mp3, wav, zip" className="mt-1.5" />
                  </div>
                </div>
              </div>

              <div className="flex gap-3 pt-6">
                <Button>
                  <Save className="w-4 h-4 mr-2" />
                  Save Settings
                </Button>
                <Button variant="outline">
                  Reset to Defaults
                </Button>
              </div>
            </CardContent>
          </Card>

          <Card>
            <CardHeader>
              <CardTitle>System Information</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Version</p>
                  <p>2.4.1</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Last Updated</p>
                  <p>November 10, 2025</p>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Database Status</p>
                  <Badge className="bg-green-100 text-green-700 hover:bg-green-100">
                    Connected
                  </Badge>
                </div>
                <div className="p-4 bg-slate-50 rounded-lg">
                  <p className="text-sm text-slate-600 mb-1">Storage Used</p>
                  <p>2.8 GB / 50 GB</p>
                </div>
              </div>
            </CardContent>
          </Card>
        </TabsContent>
      </Tabs>
    </div>
  );
}