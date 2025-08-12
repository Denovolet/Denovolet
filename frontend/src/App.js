import React, { useState, useEffect } from 'react';
import axios from 'axios';
import { Calendar } from './components/ui/calendar';
import { Button } from './components/ui/button';
import { Card, CardContent, CardHeader, CardTitle } from './components/ui/card';
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogTrigger } from './components/ui/dialog';
import { Input } from './components/ui/input';
import { Label } from './components/ui/label';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from './components/ui/select';
import { Textarea } from './components/ui/textarea';
import { Badge } from './components/ui/badge';
import { Tabs, TabsContent, TabsList, TabsTrigger } from './components/ui/tabs';
import { toast } from 'sonner';
import { Toaster } from './components/ui/sonner';
import { CalendarDays, Clock, User, Phone, Mail, Stethoscope, Settings, Plus, Edit, Trash2 } from 'lucide-react';
import { format, parseISO, startOfDay, addDays } from 'date-fns';
import { ptBR } from 'date-fns/locale';
import './App.css';

const API_URL = process.env.REACT_APP_BACKEND_URL || 'http://localhost:8001';

function App() {
  const [selectedDate, setSelectedDate] = useState(new Date());
  const [agendamentos, setAgendamentos] = useState([]);
  const [servicos, setServicos] = useState([]);
  const [horarios, setHorarios] = useState([]);
  const [horariosDisponiveis, setHorariosDisponiveis] = useState([]);
  const [loading, setLoading] = useState(false);
  
  // Estados para formulários
  const [isNovoAgendamentoOpen, setIsNovoAgendamentoOpen] = useState(false);
  const [isNovoServicoOpen, setIsNovoServicoOpen] = useState(false);
  const [isConfigHorariosOpen, setIsConfigHorariosOpen] = useState(false);
  
  // Formulário de agendamento
  const [formAgendamento, setFormAgendamento] = useState({
    paciente: { nome: '', telefone: '', email: '', observacoes: '' },
    servico_id: '',
    data_hora: '',
    observacoes: ''
  });
  
  // Formulário de serviço
  const [formServico, setFormServico] = useState({
    nome: '',
    duracao_minutos: 30,
    preco: '',
    descricao: ''
  });

  const diasSemana = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo'];

  useEffect(() => {
    carregarDados();
  }, []);

  useEffect(() => {
    carregarAgendamentos();
  }, [selectedDate]);

  const carregarDados = async () => {
    setLoading(true);
    try {
      const [servicosRes, horariosRes] = await Promise.all([
        axios.get(`${API_URL}/api/servicos`),
        axios.get(`${API_URL}/api/horarios`)
      ]);
      
      setServicos(servicosRes.data);
      setHorarios(horariosRes.data);
    } catch (error) {
      console.error('Erro ao carregar dados:', error);
      toast.error('Erro ao carregar dados do sistema');
    } finally {
      setLoading(false);
    }
  };

  const carregarAgendamentos = async () => {
    try {
      const dataFormatada = format(selectedDate, 'yyyy-MM-dd');
      const response = await axios.get(`${API_URL}/api/agendamentos?data=${dataFormatada}`);
      setAgendamentos(response.data);
    } catch (error) {
      console.error('Erro ao carregar agendamentos:', error);
      toast.error('Erro ao carregar agendamentos');
    }
  };

  const carregarHorariosDisponiveis = async (servicoId) => {
    if (!servicoId) return;
    
    try {
      const dataFormatada = format(selectedDate, 'yyyy-MM-dd');
      const response = await axios.get(`${API_URL}/api/horarios-disponiveis?data=${dataFormatada}&servico_id=${servicoId}`);
      setHorariosDisponiveis(response.data.horarios_disponiveis);
    } catch (error) {
      console.error('Erro ao carregar horários disponíveis:', error);
      toast.error('Erro ao carregar horários disponíveis');
    }
  };

  const criarAgendamento = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      const dataHora = new Date(`${format(selectedDate, 'yyyy-MM-dd')}T${formAgendamento.data_hora}`);
      
      await axios.post(`${API_URL}/api/agendamentos`, {
        ...formAgendamento,
        data_hora: dataHora.toISOString()
      });

      toast.success('Agendamento criado com sucesso!');
      setIsNovoAgendamentoOpen(false);
      setFormAgendamento({
        paciente: { nome: '', telefone: '', email: '', observacoes: '' },
        servico_id: '',
        data_hora: '',
        observacoes: ''
      });
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao criar agendamento:', error);
      toast.error(error.response?.data?.detail || 'Erro ao criar agendamento');
    } finally {
      setLoading(false);
    }
  };

  const criarServico = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await axios.post(`${API_URL}/api/servicos`, formServico);
      toast.success('Serviço criado com sucesso!');
      setIsNovoServicoOpen(false);
      setFormServico({ nome: '', duracao_minutos: 30, preco: '', descricao: '' });
      carregarDados();
    } catch (error) {
      console.error('Erro ao criar serviço:', error);
      toast.error('Erro ao criar serviço');
    } finally {
      setLoading(false);
    }
  };

  const excluirAgendamento = async (id) => {
    if (!window.confirm('Tem certeza que deseja excluir este agendamento?')) return;

    try {
      await axios.delete(`${API_URL}/api/agendamentos/${id}`);
      toast.success('Agendamento excluído com sucesso!');
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao excluir agendamento:', error);
      toast.error('Erro ao excluir agendamento');
    }
  };

  const atualizarStatusAgendamento = async (id, status) => {
    try {
      await axios.put(`${API_URL}/api/agendamentos/${id}/status`, null, {
        params: { status }
      });
      toast.success('Status atualizado com sucesso!');
      carregarAgendamentos();
    } catch (error) {
      console.error('Erro ao atualizar status:', error);
      toast.error('Erro ao atualizar status');
    }
  };

  const getStatusBadge = (status) => {
    const statusMap = {
      agendado: { label: 'Agendado', variant: 'default' },
      concluido: { label: 'Concluído', variant: 'secondary' },
      cancelado: { label: 'Cancelado', variant: 'destructive' }
    };
    
    const statusInfo = statusMap[status] || statusMap.agendado;
    return <Badge variant={statusInfo.variant}>{statusInfo.label}</Badge>;
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-green-50">
      <Toaster />
      
      {/* Header */}
      <header className="bg-white border-b border-gray-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex items-center justify-between h-16">
            <div className="flex items-center gap-3">
              <div className="bg-blue-600 p-2 rounded-xl">
                <Stethoscope className="w-6 h-6 text-white" />
              </div>
              <div>
                <h1 className="text-xl font-bold text-gray-900">Sistema de Agendamento</h1>
                <p className="text-sm text-gray-500">Clínica Odontológica</p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <Dialog open={isNovoServicoOpen} onOpenChange={setIsNovoServicoOpen}>
                <DialogTrigger asChild>
                  <Button variant="outline" size="sm">
                    <Settings className="w-4 h-4 mr-2" />
                    Serviços
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-md">
                  <DialogHeader>
                    <DialogTitle>Novo Serviço Odontológico</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={criarServico} className="space-y-4">
                    <div>
                      <Label>Nome do Serviço</Label>
                      <Input
                        value={formServico.nome}
                        onChange={(e) => setFormServico({...formServico, nome: e.target.value})}
                        placeholder="Ex: Limpeza Dental"
                        required
                      />
                    </div>
                    <div className="grid grid-cols-2 gap-4">
                      <div>
                        <Label>Duração (minutos)</Label>
                        <Input
                          type="number"
                          value={formServico.duracao_minutos}
                          onChange={(e) => setFormServico({...formServico, duracao_minutos: parseInt(e.target.value)})}
                          min="15"
                          max="180"
                        />
                      </div>
                      <div>
                        <Label>Preço (R$)</Label>
                        <Input
                          type="number"
                          step="0.01"
                          value={formServico.preco}
                          onChange={(e) => setFormServico({...formServico, preco: parseFloat(e.target.value)})}
                          placeholder="0.00"
                        />
                      </div>
                    </div>
                    <div>
                      <Label>Descrição</Label>
                      <Textarea
                        value={formServico.descricao}
                        onChange={(e) => setFormServico({...formServico, descricao: e.target.value})}
                        placeholder="Descrição do serviço..."
                        rows={3}
                      />
                    </div>
                    <div className="flex gap-2 pt-2">
                      <Button type="submit" disabled={loading} className="flex-1">
                        <Plus className="w-4 h-4 mr-2" />
                        Criar Serviço
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setIsNovoServicoOpen(false)}>
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>

              <Dialog open={isNovoAgendamentoOpen} onOpenChange={setIsNovoAgendamentoOpen}>
                <DialogTrigger asChild>
                  <Button>
                    <Plus className="w-4 h-4 mr-2" />
                    Novo Agendamento
                  </Button>
                </DialogTrigger>
                <DialogContent className="max-w-2xl">
                  <DialogHeader>
                    <DialogTitle>Novo Agendamento</DialogTitle>
                  </DialogHeader>
                  <form onSubmit={criarAgendamento} className="space-y-6">
                    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                      <div className="space-y-4">
                        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                          <User className="w-4 h-4" />
                          Dados do Paciente
                        </h3>
                        <div>
                          <Label>Nome Completo</Label>
                          <Input
                            value={formAgendamento.paciente.nome}
                            onChange={(e) => setFormAgendamento({
                              ...formAgendamento,
                              paciente: {...formAgendamento.paciente, nome: e.target.value}
                            })}
                            placeholder="Nome do paciente"
                            required
                          />
                        </div>
                        <div>
                          <Label>Telefone</Label>
                          <Input
                            value={formAgendamento.paciente.telefone}
                            onChange={(e) => setFormAgendamento({
                              ...formAgendamento,
                              paciente: {...formAgendamento.paciente, telefone: e.target.value}
                            })}
                            placeholder="(11) 99999-9999"
                            required
                          />
                        </div>
                        <div>
                          <Label>Email (opcional)</Label>
                          <Input
                            type="email"
                            value={formAgendamento.paciente.email}
                            onChange={(e) => setFormAgendamento({
                              ...formAgendamento,
                              paciente: {...formAgendamento.paciente, email: e.target.value}
                            })}
                            placeholder="email@exemplo.com"
                          />
                        </div>
                      </div>

                      <div className="space-y-4">
                        <h3 className="font-semibold text-gray-900 flex items-center gap-2">
                          <CalendarDays className="w-4 h-4" />
                          Agendamento
                        </h3>
                        <div>
                          <Label>Serviço</Label>
                          <Select
                            value={formAgendamento.servico_id}
                            onValueChange={(value) => {
                              setFormAgendamento({...formAgendamento, servico_id: value});
                              carregarHorariosDisponiveis(value);
                            }}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione um serviço" />
                            </SelectTrigger>
                            <SelectContent>
                              {servicos.map((servico) => (
                                <SelectItem key={servico.id} value={servico.id}>
                                  {servico.nome} - {servico.duracao_minutos}min
                                  {servico.preco && ` - R$ ${servico.preco.toFixed(2)}`}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>

                        <div>
                          <Label>Data: {format(selectedDate, 'dd/MM/yyyy', { locale: ptBR })}</Label>
                          <p className="text-sm text-gray-500 mt-1">Use o calendário para selecionar outra data</p>
                        </div>

                        <div>
                          <Label>Horário</Label>
                          <Select
                            value={formAgendamento.data_hora}
                            onValueChange={(value) => setFormAgendamento({...formAgendamento, data_hora: value})}
                            disabled={!formAgendamento.servico_id}
                          >
                            <SelectTrigger>
                              <SelectValue placeholder="Selecione um horário" />
                            </SelectTrigger>
                            <SelectContent>
                              {horariosDisponiveis.map((horario) => (
                                <SelectItem key={horario} value={horario}>
                                  {horario}
                                </SelectItem>
                              ))}
                            </SelectContent>
                          </Select>
                        </div>
                      </div>
                    </div>

                    <div>
                      <Label>Observações (opcional)</Label>
                      <Textarea
                        value={formAgendamento.observacoes}
                        onChange={(e) => setFormAgendamento({...formAgendamento, observacoes: e.target.value})}
                        placeholder="Observações sobre o agendamento..."
                        rows={3}
                      />
                    </div>

                    <div className="flex gap-2 pt-2">
                      <Button type="submit" disabled={loading} className="flex-1">
                        <CalendarDays className="w-4 h-4 mr-2" />
                        Confirmar Agendamento
                      </Button>
                      <Button type="button" variant="outline" onClick={() => setIsNovoAgendamentoOpen(false)}>
                        Cancelar
                      </Button>
                    </div>
                  </form>
                </DialogContent>
              </Dialog>
            </div>
          </div>
        </div>
      </header>

      {/* Main Content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Calendar Section */}
          <div className="lg:col-span-1">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <CalendarDays className="w-5 h-5" />
                  Calendário
                </CardTitle>
              </CardHeader>
              <CardContent>
                <Calendar
                  mode="single"
                  selected={selectedDate}
                  onSelect={setSelectedDate}
                  locale={ptBR}
                  className="rounded-md border"
                />
                <div className="mt-4 p-3 bg-blue-50 rounded-lg">
                  <p className="text-sm text-blue-800 font-medium">
                    Data selecionada: {format(selectedDate, 'dd/MM/yyyy', { locale: ptBR })}
                  </p>
                  <p className="text-sm text-blue-600">
                    {agendamentos.length} agendamento(s) neste dia
                  </p>
                </div>
              </CardContent>
            </Card>

            {/* Serviços Disponíveis */}
            <Card className="mt-6">
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Stethoscope className="w-5 h-5" />
                  Serviços Disponíveis
                </CardTitle>
              </CardHeader>
              <CardContent>
                <div className="space-y-3">
                  {servicos.slice(0, 5).map((servico) => (
                    <div key={servico.id} className="p-3 border rounded-lg">
                      <div className="flex items-center justify-between">
                        <h4 className="font-medium text-gray-900">{servico.nome}</h4>
                        {servico.preco && (
                          <span className="text-sm font-semibold text-green-600">
                            R$ {servico.preco.toFixed(2)}
                          </span>
                        )}
                      </div>
                      <div className="flex items-center gap-4 mt-1 text-sm text-gray-500">
                        <span className="flex items-center gap-1">
                          <Clock className="w-3 h-3" />
                          {servico.duracao_minutos} min
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </CardContent>
            </Card>
          </div>

          {/* Appointments Section */}
          <div className="lg:col-span-2">
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <Clock className="w-5 h-5" />
                  Agendamentos - {format(selectedDate, 'dd/MM/yyyy', { locale: ptBR })}
                </CardTitle>
              </CardHeader>
              <CardContent>
                {agendamentos.length === 0 ? (
                  <div className="text-center py-12">
                    <CalendarDays className="w-16 h-16 text-gray-300 mx-auto mb-4" />
                    <h3 className="text-lg font-medium text-gray-900 mb-2">Nenhum agendamento</h3>
                    <p className="text-gray-500 mb-4">Não há agendamentos para esta data.</p>
                    <Button onClick={() => setIsNovoAgendamentoOpen(true)}>
                      <Plus className="w-4 h-4 mr-2" />
                      Criar Primeiro Agendamento
                    </Button>
                  </div>
                ) : (
                  <div className="space-y-4">
                    {agendamentos
                      .sort((a, b) => new Date(a.data_hora) - new Date(b.data_hora))
                      .map((agendamento) => (
                      <div key={agendamento.id} className="border rounded-lg p-4 hover:shadow-md transition-shadow">
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <div className="flex items-center gap-3 mb-2">
                              <div className="flex items-center gap-1 text-blue-600 font-medium">
                                <Clock className="w-4 h-4" />
                                {format(parseISO(agendamento.data_hora), 'HH:mm')}
                              </div>
                              {getStatusBadge(agendamento.status)}
                            </div>
                            
                            <h3 className="font-semibold text-gray-900 mb-1">{agendamento.paciente.nome}</h3>
                            <p className="text-sm text-gray-600 mb-2">{agendamento.servico_nome}</p>
                            
                            <div className="flex items-center gap-4 text-sm text-gray-500">
                              <span className="flex items-center gap-1">
                                <Phone className="w-3 h-3" />
                                {agendamento.paciente.telefone}
                              </span>
                              {agendamento.paciente.email && (
                                <span className="flex items-center gap-1">
                                  <Mail className="w-3 h-3" />
                                  {agendamento.paciente.email}
                                </span>
                              )}
                            </div>
                            
                            {agendamento.observacoes && (
                              <p className="text-sm text-gray-600 mt-2 p-2 bg-gray-50 rounded">
                                {agendamento.observacoes}
                              </p>
                            )}
                          </div>
                          
                          <div className="flex items-center gap-2 ml-4">
                            {agendamento.status === 'agendado' && (
                              <>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => atualizarStatusAgendamento(agendamento.id, 'concluido')}
                                >
                                  Concluir
                                </Button>
                                <Button
                                  size="sm"
                                  variant="outline"
                                  onClick={() => atualizarStatusAgendamento(agendamento.id, 'cancelado')}
                                >
                                  Cancelar
                                </Button>
                              </>
                            )}
                            <Button
                              size="sm"
                              variant="outline"
                              onClick={() => excluirAgendamento(agendamento.id)}
                            >
                              <Trash2 className="w-4 h-4" />
                            </Button>
                          </div>
                        </div>
                      </div>
                    ))}
                  </div>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      </main>
    </div>
  );
}

export default App;