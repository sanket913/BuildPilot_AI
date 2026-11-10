import { afterEach, describe, expect, it, vi } from 'vitest'
import { cleanup, fireEvent, render, screen, waitFor } from '@testing-library/react'
import App from './App'

afterEach(()=>{cleanup();vi.unstubAllGlobals();location.hash='';sessionStorage.clear()})
function mockApi(){
  vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
    const url=String(input)
    const data=url.endsWith('/health')?{status:'ok',ai_mode:'demo'}:url.endsWith('/demo')?{available:true,project_id:7}:url.endsWith('/integrations/nonilion')?{configured:false,message:'Not configured'}:[]
    return {ok:true,status:200,json:async()=>data}
  }))
}
describe('workspace onboarding and navigation',()=>{
  it('shows onboarding and opens the four-step project flow',async()=>{
    mockApi();render(<App/>)
    expect(await screen.findByRole('heading',{name:/welcome to buildpilot ai/i})).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:/create project/i}))
    expect(await screen.findByRole('heading',{name:/create your project/i})).toBeTruthy()
    expect(screen.getByLabelText(/project name/i)).toBeTruthy()
  })
  it('starts the brief analyzer blank until a project or sample is selected',async()=>{
    mockApi();location.hash='#ai-problem-analyzer';render(<App/>);
    expect(await screen.findByRole('heading',{name:/turn a brief into a build plan/i})).toBeTruthy()
    expect((screen.getByLabelText('Problem statement') as HTMLTextAreaElement).value).toBe('')
    expect(screen.queryByText(/Campus Food Loop/i)).toBeNull()
  })
  it('shows saved projects and filters them using their actual fields',async()=>{
    const project={id:17,name:'Real launch workspace',description:'A saved project description',hackathon_name:'Campus Build Day',start_date:null,deadline:null,status:'In Progress',archived:false,is_demo:false,problem_statement:'',analysis:null,solution:null,tasks:[],members:[],checks:[],documents:[],activities:[]}
    vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
      const url=String(input)
      const data=url.endsWith('/health')?{status:'ok',ai_mode:'demo'}:url.endsWith('/demo')?{available:false,project_id:null}:url.endsWith('/integrations/nonilion')?{configured:false,message:'Not configured'}:url.endsWith('/projects/17/risks')?{risks:[]}:url.endsWith('/projects')?[project]:project
      return {ok:true,status:200,json:async()=>data}
    }))
    render(<App/>);fireEvent.click(await screen.findByRole('link',{name:/my projects/i}))
    expect(await screen.findByRole('heading',{name:'Real launch workspace'})).toBeTruthy()
    expect(screen.getByText('Campus Build Day')).toBeTruthy()
    fireEvent.change(screen.getByRole('textbox',{name:/search projects/i}),{target:{value:'nothing matches'}})
    expect(screen.getByRole('heading',{name:/no matching workspaces/i})).toBeTruthy()
    expect(screen.getByText('0 workspaces')).toBeTruthy()
  })
  it('navigates to projects from the sidebar',async()=>{
    mockApi();render(<App/>)
    fireEvent.click(await screen.findByRole('link',{name:/my projects/i}))
    await waitFor(()=>expect(screen.getByRole('heading',{name:/projects with momentum/i})).toBeTruthy())
  })
  it('asks for the configured shared access code and rejects an invalid one',async()=>{
    const fetchMock=vi.fn(async(input:RequestInfo|URL,init?:RequestInit)=>{
      const url=String(input)
      if(url.endsWith('/health'))return {ok:true,status:200,json:async()=>({status:'ok',ai_mode:'demo',access_controlled:true})}
      return {ok:false,status:401,json:async()=>({detail:'Workspace access code required'}),headers:new Headers()}
    })
    vi.stubGlobal('fetch',fetchMock)
    render(<App/>)
    const input=await screen.findByLabelText(/access code/i)
    fireEvent.change(input,{target:{value:'incorrect-code'}})
    fireEvent.click(screen.getByRole('button',{name:/continue/i}))
    expect((await screen.findByRole('alert')).textContent).toMatch(/not accepted/i)
    expect(fetchMock.mock.calls.some(([,init])=>new Headers(init?.headers).get('Authorization')==='Bearer incorrect-code')).toBe(true)
  })
  it('lets the user explore the 3D project map by phase',async()=>{
    const project={id:7,name:'Demo workspace',description:'A sample',hackathon_name:'Build sprint',status:'In Progress',archived:false,is_demo:false,problem_statement:'Sample challenge',analysis:{title:'Sample challenge',summary:'Plan and build.'},solution:{},members:[],tasks:[{id:1,title:'Plan user flow',description:'Confirm users.',status:'Completed',priority:'High',assignee:'',due_date:null,phase:'Research and planning',dependencies:'',acceptance_criteria:'',estimated_effort:'2 hours'},{id:2,title:'Build API',description:'Implement the endpoint.',status:'In Progress',priority:'Critical',assignee:'',due_date:null,phase:'Core development',dependencies:'',acceptance_criteria:'',estimated_effort:'4 hours'}],checks:[],documents:[],activities:[]}
    vi.stubGlobal('fetch',vi.fn(async(input:RequestInfo|URL)=>{
      const url=String(input)
      const data=url.endsWith('/health')?{status:'ok',ai_mode:'demo'}:url.endsWith('/demo')?{available:true,project_id:7}:url.endsWith('/integrations/nonilion')?{configured:false,message:'Not configured'}:url.endsWith('/projects')?[project]:url.endsWith('/projects/7/risks')?{mode:'rule_based_recommendations',risks:[]}:project
      return {ok:true,status:200,json:async()=>data}
    }))
    render(<App/>)
    expect(await screen.findByRole('heading',{name:/build your project/i})).toBeTruthy()
    const phase=screen.getByRole('button',{name:/core development/i})
    fireEvent.click(phase)
    expect(phase.getAttribute('aria-pressed')).toBe('true')
    expect(screen.getByRole('heading',{name:'Core development'})).toBeTruthy()
    fireEvent.click(screen.getByRole('button',{name:/explore roadmap/i}))
    await waitFor(()=>expect(screen.getByRole('heading',{name:/see the path.*ship with focus/i})).toBeTruthy())
  })
})
